import json
import logging
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.graduate.api_security import PredictionApiSecurityMixin
from apps.graduate.api_serializers import (
    CrossModuleQuerySerializer,
    GlobalSearchQuerySerializer,
    PredictionAnalyzeRequestSerializer,
    PredictionChatRequestSerializer,
    PredictionContextQuerySerializer,
)
from apps.graduate import services
from apps.graduate import upload_services
from apps.graduate import upload_pipeline
from apps.graduate import export_services
from apps.graduate import warning_services
from apps.graduate.models import (
    ImportBatch,
    ImportBatchStatus,
    ImportMappingTemplate,
    FieldCatalog,
    ExportTemplate,
    ExportRecord,
    WarningRule,
    WarningInstance,
    WarningTreatmentLog,
)


logger = logging.getLogger(__name__)


class GraduateBaseView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "public_read"
    builder = None

    def get(self, request):
        return Response(self.builder())


class SharedOptionsView(GraduateBaseView):
    builder = staticmethod(services.get_shared_options_data)


class HomeDataView(GraduateBaseView):
    builder = staticmethod(services.get_home_data)


class AdmissionDataView(GraduateBaseView):
    builder = staticmethod(services.get_admission_data)


class AcademicStatusDataView(GraduateBaseView):
    builder = staticmethod(services.get_academic_status_data)


class AcademicChangeDataView(GraduateBaseView):
    builder = staticmethod(services.get_academic_change_data)


class TrainingDataView(GraduateBaseView):
    builder = staticmethod(services.get_training_data)


class TrainingCourseDataView(GraduateBaseView):
    builder = staticmethod(services.get_training_course_data)


class DegreeDataView(GraduateBaseView):
    builder = staticmethod(services.get_degree_data)


class DegreeDefenseDataView(GraduateBaseView):
    builder = staticmethod(services.get_degree_defense_data)


class ScholarshipDataView(GraduateBaseView):
    builder = staticmethod(services.get_scholarship_data)


class EmploymentDataView(GraduateBaseView):
    builder = staticmethod(services.get_employment_data)


class IntelligentPredictionDataView(GraduateBaseView):
    security_scope = "prediction_data"
    builder = staticmethod(services.get_intelligent_prediction_data)


class PredictionContextView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "prediction_context"

    def get(self, request):
        serializer = PredictionContextQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        student_id = serializer.validated_data["student_id"]

        payload = services.get_intelligent_prediction_context(student_id)
        if payload is None:
            return Response(
                {"detail": "prediction context not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(payload)


class PredictionAnalyzeView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "prediction_analyze"

    def post(self, request):
        serializer = PredictionAnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        payload = services.get_intelligent_prediction_analysis(
            student_id=validated["studentId"],
            tab=validated.get("tab", "trend"),
            experiment_key=validated.get("experimentKey", "default"),
            runtime_options=validated.get("runtimeOptions", {}),
        )
        if payload is None:
            return Response(
                {"detail": "prediction analysis not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(payload)


class PredictionChatView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "prediction_chat"

    def post(self, request):
        serializer = PredictionChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        payload = services.get_intelligent_prediction_chat(
            student_id=validated["studentId"],
            question=validated["question"],
            chat_history=validated.get("chatHistory", []),
            experiment_key=validated.get("experimentKey", "default"),
            runtime_options=validated.get("runtimeOptions", {}),
        )
        if payload is None:
            return Response(
                {"detail": "prediction chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(payload)


class PredictionChatStreamView(PredictionApiSecurityMixin, APIView):
    """SSE 流式问答。

    Agent 单次问答要 10~40s，一次性返回会让前端像卡住，
    所以这里把工具调用过程逐步推给前端。
    事件格式：每行 `data: {...}\n\n`，最后以 `data: [DONE]` 收尾。
    """

    permission_classes = [AllowAny]
    security_scope = "prediction_chat"

    def post(self, request):
        serializer = PredictionChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        event_stream = services.stream_intelligent_prediction_chat(
            student_id=validated["studentId"],
            question=validated["question"],
            chat_history=validated.get("chatHistory", []),
            experiment_key=validated.get("experimentKey", "default"),
            runtime_options=validated.get("runtimeOptions", {}),
        )
        if event_stream is None:
            return Response(
                {"detail": "prediction chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        def sse_lines():
            try:
                for event in event_stream:
                    yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            except Exception as exc:
                # 流已经开始后无法再改 HTTP 状态码，
                # 只能把错误作为一个事件推下去，让前端自行降级提示。
                logger.exception("prediction chat stream failed")
                error_event = {"type": "error", "reason": "stream_failed", "error": str(exc)}
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(
            sse_lines(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        # 关掉 nginx 等反代的缓冲，否则 SSE 会被攒成一整包再下发
        response["X-Accel-Buffering"] = "no"
        return response


class GlobalSearchView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "public_search"

    def get(self, request):
        serializer = GlobalSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(services.get_global_search_data(serializer.validated_data.get("q", "")))


class CrossModuleQueryView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "public_query"

    def get(self, request):
        serializer = CrossModuleQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        return Response(
            services.get_cross_module_query_data(
                grade=validated.get("grade", ""),
                major=validated.get("major", ""),
            )
        )


# ============================================================
# R05: Data Upload Views
# ============================================================

class UploadFileView(APIView):
    permission_classes = []  # 临时禁用认证，方便测试

    def post(self, request):
        """文件上传接口"""
        # 临时注释权限检查，方便测试
        # if not hasattr(request.user, 'role') or request.user.role != 'admin':
        #     return Response(
        #         {'error': '仅管理员可以上传文件'},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        # 获取上传的文件
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': '未找到上传文件'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证文件扩展名
        file_name = file_obj.name
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in ['.xlsx', '.csv', '.xls']:
            return Response(
                {'error': '仅支持 xlsx、xls 和 csv 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证文件大小（50MB）
        max_size = 50 * 1024 * 1024
        if file_obj.size > max_size:
            return Response(
                {'error': '文件大小不能超过 50MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 保存文件到临时目录
        tmp_dir = Path(settings.BASE_DIR) / 'tmp' / 'uploads'
        tmp_dir.mkdir(parents=True, exist_ok=True)

        batch_id = str(uuid.uuid4())
        file_path = tmp_dir / f"{batch_id}_{file_name}"

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # 计算文件哈希
        file_hash = upload_services.calculate_file_hash(str(file_path))

        # 检查是否重复上传
        duplicate_batch = upload_services.check_duplicate(file_hash)

        # 解析文件
        try:
            parsed_data = upload_services.parse_workbook(str(file_path))
        except Exception as e:
            return Response(
                {'error': f'文件解析失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建导入批次
        # 获取或创建一个默认用户用于测试
        from django.contrib.auth import get_user_model
        User = get_user_model()
        test_user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={'email': 'test@example.com', 'role': 'admin'}
        )

        import_batch = ImportBatch.objects.create(
            batch_id=batch_id,
            file_name=file_name,
            file_hash=file_hash,
            status=ImportBatchStatus.DRAFT,
            operator=test_user,  # 使用测试用户
            started_at=timezone.now()
        )

        return Response({
            'batch_id': batch_id,
            'file_name': file_name,
            'file_hash': file_hash,
            'duplicate': duplicate_batch is not None,
            'sheets': parsed_data.get('sheets', [])
        })


class SheetIdentifyView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """Sheet 模块识别接口"""
        batch_id = request.data.get('batch_id')
        manual_module = request.data.get('manual_module')  # 人工指定的模块

        if not batch_id:
            return Response(
                {'error': 'batch_id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            batch = ImportBatch.objects.get(batch_id=batch_id)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 读取文件
        tmp_dir = Path(settings.BASE_DIR) / 'tmp' / 'uploads'
        file_path = tmp_dir / f"{batch_id}_{batch.file_name}"

        if not file_path.exists():
            return Response(
                {'error': '文件不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            identification_results = upload_pipeline.identify_sheets(batch, manual_module)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)

        # 更新批次状态
        batch.status = ImportBatchStatus.MAPPING
        batch.save()

        return Response({
            'batch_id': batch_id,
            'identification_results': identification_results
        })


class FieldMappingView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """字段映射接口"""
        batch_id = request.data.get('batch_id')
        sheet_name = request.data.get('sheet_name')
        mapping = request.data.get('mapping', {})  # {文件列名: 字段编码}

        if not batch_id or not isinstance(mapping, dict):
            return Response(
                {'error': 'batch_id 和 mapping 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            batch = ImportBatch.objects.get(batch_id=batch_id)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            upload_pipeline.save_mapping(batch, sheet_name, mapping)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)

        # 更新批次状态
        batch.status = ImportBatchStatus.VALIDATING
        batch.save()

        return Response({
            'batch_id': batch_id,
            'mapping': mapping,
            'message': '映射保存成功'
        })

    def get(self, request):
        """获取当前批次的映射状态"""
        batch_id = request.query_params.get('batch_id')

        if not batch_id:
            return Response(
                {'error': 'batch_id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            batch = ImportBatch.objects.get(batch_id=batch_id)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            plan = upload_pipeline.load_plan(batch)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        return Response({'batch_id': batch_id, 'status': batch.status, 'sheets': plan['sheets']})



class ValidateAndPreviewView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """校验和预览接口"""
        batch_id = request.data.get('batch_id')
        strategy = request.data.get('strategy', 'create_only')  # create_only / update_empty / overwrite / validate_only

        if not batch_id:
            return Response(
                {'error': 'batch_id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            batch = ImportBatch.objects.get(batch_id=batch_id)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if batch.status == ImportBatchStatus.COMPLETED:
            return Response({'error': '该批次已完成，请勿重复导入'}, status=400)
        try:
            result = upload_pipeline.prepare_import(batch, strategy)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        batch.status = ImportBatchStatus.PREVIEWING
        upload_pipeline.remember_preview(batch, strategy)
        for field in ('total_rows', 'new_count', 'update_count', 'unchanged_count', 'error_count', 'skipped_count'):
            setattr(batch, field, result['preview'][field])
        batch.save()
        return Response({'batch_id': batch_id, 'validation': result['validation'], 'preview': result['preview']})



class ConfirmImportView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """确认导入接口"""
        batch_id = request.data.get('batch_id')
        strategy = request.data.get('strategy', 'create_only')

        if not batch_id:
            return Response(
                {'error': 'batch_id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            batch = ImportBatch.objects.get(batch_id=batch_id)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if batch.status != ImportBatchStatus.PREVIEWING:
            return Response({'error': '请先执行校验预览，请勿重复导入'}, status=400)
        try:
            result = upload_pipeline.execute_batch(batch, strategy)
        except Exception as exc:
            logger.exception('Import failed for batch %s', batch_id)
            return Response({'error': f'导入失败，数据已回滚：{exc}'}, status=400)
        return Response(result)



class ImportBatchListView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取导入批次列表"""
        batches = ImportBatch.objects.all().order_by('-created_at')

        # 筛选
        status_filter = request.query_params.get('status')
        if status_filter:
            batches = batches.filter(status=status_filter)

        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        start = (page - 1) * page_size
        end = start + page_size

        total = batches.count()
        batch_list = []

        for batch in batches[start:end]:
            batch_list.append({
                'id': batch.id,
                'batch_id': batch.batch_id,
                'file_name': batch.file_name,
                'status': batch.status,
                'operator': batch.operator.username if batch.operator else None,
                'total_rows': batch.total_rows,
                'new_count': batch.new_count,
                'update_count': batch.update_count,
                'error_count': batch.error_count,
                'created_at': batch.created_at.isoformat(),
                'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
            })

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': batch_list
        })


class ImportBatchDetailView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request, pk):
        """获取导入批次详情"""
        try:
            batch = ImportBatch.objects.get(pk=pk)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 获取记录摘要（前100条）
        records = batch.records.all()[:100]
        record_list = []

        for record in records:
            record_list.append({
                'row_index': record.row_index,
                'action': record.action,
                'target_model': record.target_model,
                'target_id': record.target_id,
                'errors': record.errors,
                'is_reverted': record.is_reverted,
            })

        return Response({
            'id': batch.id,
            'batch_id': batch.batch_id,
            'file_name': batch.file_name,
            'status': batch.status,
            'operator': batch.operator.username if batch.operator else None,
            'total_rows': batch.total_rows,
            'new_count': batch.new_count,
            'update_count': batch.update_count,
            'unchanged_count': batch.unchanged_count,
            'error_count': batch.error_count,
            'skipped_count': batch.skipped_count,
            'error_summary': batch.error_summary,
            'source_module': batch.source_module,
            'created_at': batch.created_at.isoformat(),
            'started_at': batch.started_at.isoformat() if batch.started_at else None,
            'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
            'records': record_list
        })


class RevertBatchView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """撤销批次导入"""
        batch_id = request.data.get('batch_id')

        if not batch_id:
            return Response(
                {'error': 'batch_id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            batch = ImportBatch.objects.get(batch_id=batch_id)
        except ImportBatch.DoesNotExist:
            return Response(
                {'error': '批次不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 执行撤销
        revert_result = upload_services.revert_batch(batch_id)

        return Response(revert_result)


class MappingTemplateView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取映射模板列表"""
        templates = ImportMappingTemplate.objects.filter(
            is_public=True
        ) | ImportMappingTemplate.objects.filter(
            created_by=request.user
        )

        template_list = []
        for template in templates:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'target_module': template.target_module,
                'version': template.version,
                'is_public': template.is_public,
                'created_at': template.created_at.isoformat(),
            })

        return Response({
            'results': template_list
        })

    def post(self, request):
        """保存映射模板"""
        name = request.data.get('name')
        target_module = request.data.get('target_module')
        mapping = request.data.get('mapping', {})

        if not name or not target_module:
            return Response(
                {'error': 'name 和 target_module 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        template = ImportMappingTemplate.objects.create(
            name=name,
            target_module=target_module,
            mapping=mapping,
            created_by=request.user
        )

        return Response({
            'id': template.id,
            'name': template.name,
            'message': '模板保存成功'
        })

    def delete(self, request):
        """删除映射模板"""
        template_id = request.query_params.get('id')

        if not template_id:
            return Response(
                {'error': 'id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            template = ImportMappingTemplate.objects.get(id=template_id, created_by=request.user)
            template.delete()
            return Response({'message': '模板删除成功'})
        except ImportMappingTemplate.DoesNotExist:
            return Response(
                {'error': '模板不存在或无权限删除'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================================
# R06: Export Views
# ============================================================

class ExportFieldsView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取可导出字段列表"""
        fields = export_services.get_exportable_fields()
        return Response({'fields': fields})


class StudentListExportView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """导出学生名单"""
        fields = request.data.get('fields', [])
        filters = request.data.get('filters', {})
        one_to_many_strategies = request.data.get('one_to_many_strategies', {})
        field_aliases = request.data.get('field_aliases', {})

        if not fields:
            return Response(
                {'error': 'fields 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 预计人数
        students = export_services.build_student_queryset(filters, request.user)
        estimated_count = students.count()

        # 小数据量同步生成
        if estimated_count < 5000:
            try:
                result = export_services.generate_student_list_excel(
                    fields,
                    filters,
                    one_to_many_strategies,
                    field_aliases,
                    request.user
                )
                return Response({
                    'status': 'completed',
                    'record_id': result['record_id'],
                    'file_name': result['file_name'],
                    'row_count': result['row_count'],
                    'estimated_count': estimated_count
                })
            except Exception as e:
                return Response(
                    {'error': f'导出失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # 大数据量返回任务ID
            return Response({
                'status': 'pending',
                'estimated_count': estimated_count,
                'message': '数据量较大，请稍后查看导出记录'
            })


class SummaryTableExportView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """导出汇总表"""
        filters = request.data.get('filters', {})

        try:
            result = export_services.generate_summary_table_excel(
                filters,
                request.user
            )
            return Response({
                'status': 'completed',
                'record_id': result['record_id'],
                'file_name': result['file_name'],
                'row_count': result['row_count']
            })
        except Exception as e:
            return Response(
                {'error': f'导出失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportRecordListView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取导出记录列表"""
        records = ExportRecord.objects.filter(operator=request.user).order_by('-created_at')

        # 筛选
        status_filter = request.query_params.get('status')
        if status_filter:
            records = records.filter(status=status_filter)

        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        start = (page - 1) * page_size
        end = start + page_size

        total = records.count()
        record_list = []

        for record in records[start:end]:
            # 检查是否过期
            is_expired = False
            if record.expires_at and timezone.now() > record.expires_at:
                is_expired = True
                if record.status != 'expired':
                    record.status = 'expired'
                    record.save()

            record_list.append({
                'id': record.id,
                'record_id': record.record_id,
                'file_name': record.file_name,
                'export_type': record.export_type,
                'status': record.status,
                'row_count': record.row_count,
                'created_at': record.created_at.isoformat(),
                'expires_at': record.expires_at.isoformat() if record.expires_at else None,
                'is_expired': is_expired,
                'download_url': f'/api/v1/export/download/{record.record_id}/' if not is_expired else None
            })

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': record_list
        })


class ExportTemplateView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取导出模板列表"""
        templates = ExportTemplate.objects.filter(
            is_public=True
        ) | ExportTemplate.objects.filter(
            owner=request.user
        )

        template_list = []
        for template in templates:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'version': template.version,
                'is_public': template.is_public,
                'fields': template.fields,
                'filters': template.filters,
                'created_at': template.created_at.isoformat(),
            })

        return Response({
            'results': template_list
        })

    def post(self, request):
        """保存导出模板"""
        name = request.data.get('name')
        fields = request.data.get('fields', [])
        filters = request.data.get('filters', {})
        field_aliases = request.data.get('field_aliases', {})
        one_to_many_strategy = request.data.get('one_to_many_strategy', {})

        if not name:
            return Response(
                {'error': 'name 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        template = ExportTemplate.objects.create(
            name=name,
            owner=request.user,
            fields=fields,
            filters=filters,
            field_aliases=field_aliases,
            one_to_many_strategy=one_to_many_strategy
        )

        return Response({
            'id': template.id,
            'name': template.name,
            'message': '模板保存成功'
        })

    def delete(self, request):
        """删除导出模板"""
        template_id = request.query_params.get('id')

        if not template_id:
            return Response(
                {'error': 'id 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            template = ExportTemplate.objects.get(id=template_id, owner=request.user)
            template.delete()
            return Response({'message': '模板删除成功'})
        except ExportTemplate.DoesNotExist:
            return Response(
                {'error': '模板不存在或无权限删除'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================================
# R07: Warning Rule Engine Views
# ============================================================

class WarningRuleListView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取预警规则列表"""
        rules = WarningRule.objects.all()

        # 筛选
        module_filter = request.query_params.get('module')
        if module_filter:
            rules = rules.filter(target_module=module_filter)

        status_filter = request.query_params.get('status')
        if status_filter:
            is_active = status_filter == 'active'
            rules = rules.filter(is_active=is_active)

        risk_level_filter = request.query_params.get('risk_level')
        if risk_level_filter:
            rules = rules.filter(risk_level=risk_level_filter)

        rule_list = []
        for rule in rules:
            rule_list.append({
                'id': rule.id,
                'name': rule.name,
                'code': rule.code,
                'description': rule.description,
                'target_module': rule.target_module,
                'indicator_field': rule.indicator_field,
                'operator': rule.operator,
                'threshold_value': rule.threshold_value,
                'risk_level': rule.risk_level,
                'is_active': rule.is_active,
                'version': rule.version,
                'created_at': rule.created_at.isoformat(),
            })

        return Response({'results': rule_list})

    def post(self, request):
        """创建预警规则（仅管理员）"""
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response(
                {'error': '仅管理员可以创建规则'},
                status=status.HTTP_403_FORBIDDEN
            )

        name = request.data.get('name')
        code = request.data.get('code')
        indicator_field = request.data.get('indicator_field')
        operator = request.data.get('operator')
        threshold_value = request.data.get('threshold_value')
        risk_level = request.data.get('risk_level')

        if not all([name, code, indicator_field, operator, threshold_value, risk_level]):
            return Response(
                {'error': '缺少必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rule = WarningRule.objects.create(
            name=name,
            code=code,
            description=request.data.get('description', ''),
            target_module=request.data.get('target_module', ''),
            indicator_field=indicator_field,
            operator=operator,
            threshold_value=threshold_value,
            risk_level=risk_level,
            created_by=request.user
        )

        return Response({
            'id': rule.id,
            'message': '规则创建成功'
        })


class WarningRuleDetailView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request, pk):
        """获取规则详情"""
        try:
            rule = WarningRule.objects.get(pk=pk)
        except WarningRule.DoesNotExist:
            return Response(
                {'error': '规则不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'id': rule.id,
            'name': rule.name,
            'code': rule.code,
            'description': rule.description,
            'target_module': rule.target_module,
            'indicator_field': rule.indicator_field,
            'operator': rule.operator,
            'threshold_value': rule.threshold_value,
            'risk_level': rule.risk_level,
            'is_active': rule.is_active,
            'version': rule.version,
            'created_at': rule.created_at.isoformat(),
        })

    def put(self, request, pk):
        """修改规则（自动创建新版本）"""
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response(
                {'error': '仅管理员可以修改规则'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            rule = WarningRule.objects.get(pk=pk)
        except WarningRule.DoesNotExist:
            return Response(
                {'error': '规则不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 更新规则并增加版本号
        if 'name' in request.data:
            rule.name = request.data['name']
        if 'description' in request.data:
            rule.description = request.data['description']
        if 'indicator_field' in request.data:
            rule.indicator_field = request.data['indicator_field']
        if 'operator' in request.data:
            rule.operator = request.data['operator']
        if 'threshold_value' in request.data:
            rule.threshold_value = request.data['threshold_value']
        if 'risk_level' in request.data:
            rule.risk_level = request.data['risk_level']

        rule.version += 1
        rule.save()

        return Response({
            'id': rule.id,
            'version': rule.version,
            'message': '规则修改成功'
        })

    def patch(self, request, pk):
        """启停规则"""
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response(
                {'error': '仅管理员可以启停规则'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            rule = WarningRule.objects.get(pk=pk)
        except WarningRule.DoesNotExist:
            return Response(
                {'error': '规则不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        is_active = request.data.get('is_active')
        if is_active is not None:
            rule.is_active = is_active
            rule.save()

        return Response({
            'id': rule.id,
            'is_active': rule.is_active,
            'message': '规则状态更新成功'
        })


class WarningScanView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request):
        """触发预警扫描"""
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response(
                {'error': '仅管理员可以触发扫描'},
                status=status.HTTP_403_FORBIDDEN
            )

        dry_run = request.data.get('dry_run', False)
        rule_ids = request.data.get('rule_ids')

        result = warning_services.run_scan(rule_ids=rule_ids, dry_run=dry_run)

        return Response(result)


class WarningInstanceListView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取预警列表"""
        warnings = WarningInstance.objects.all()

        # 根据角色过滤
        if hasattr(request.user, 'role'):
            if request.user.role == 'teacher':
                # 教师只看自己学生的预警
                warnings = warnings.filter(student__advisor_name=request.user.username)
            elif request.user.role == 'student':
                # 学生只看自己的预警
                warnings = warnings.filter(student__student_id=request.user.username)

        # 筛选
        student_id = request.query_params.get('student_id')
        if student_id:
            warnings = warnings.filter(student__student_id=student_id)

        rule_id = request.query_params.get('rule_id')
        if rule_id:
            warnings = warnings.filter(rule_id=rule_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            warnings = warnings.filter(status=status_filter)

        risk_level = request.query_params.get('risk_level')
        if risk_level:
            warnings = warnings.filter(rule__risk_level=risk_level)

        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        start = (page - 1) * page_size
        end = start + page_size

        total = warnings.count()
        warning_list = []

        for warning in warnings[start:end]:
            warning_list.append({
                'id': warning.id,
                'rule_name': warning.rule.name,
                'rule_code': warning.rule.code,
                'student_id': warning.student.student_id,
                'student_name': warning.student.name,
                'indicator_value': warning.indicator_value,
                'threshold': warning.threshold_at_hit,
                'risk_level': warning.rule.risk_level,
                'status': warning.status,
                'data_time': warning.data_time.isoformat(),
                'hit_at': warning.hit_at.isoformat(),
                'resolved_at': warning.resolved_at.isoformat() if warning.resolved_at else None,
            })

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': warning_list
        })


class WarningInstanceDetailView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request, pk):
        """获取预警详情"""
        try:
            warning = WarningInstance.objects.get(pk=pk)
        except WarningInstance.DoesNotExist:
            return Response(
                {'error': '预警不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 生成解释
        generate_explanation = request.query_params.get('generate_explanation', 'false') == 'true'
        explanation = None

        if generate_explanation:
            explanation = warning_services.generate_explanation(warning)

        # 获取处理记录
        treatment_logs = warning.treatment_logs.all()
        log_list = []
        for log in treatment_logs:
            log_list.append({
                'action': log.action,
                'operator': log.operator.username if log.operator else 'System',
                'note': log.note,
                'created_at': log.created_at.isoformat(),
            })

        return Response({
            'id': warning.id,
            'rule': {
                'name': warning.rule.name,
                'code': warning.rule.code,
                'version': warning.rule_version.version,
                'snapshot': warning.rule_version.snapshot,
            },
            'student': {
                'student_id': warning.student.student_id,
                'name': warning.student.name,
                'grade': warning.student.grade,
                'major': warning.student.major,
            },
            'indicator_value': warning.indicator_value,
            'threshold': warning.threshold_at_hit,
            'risk_level': warning.rule.risk_level,
            'status': warning.status,
            'data_time': warning.data_time.isoformat(),
            'hit_at': warning.hit_at.isoformat(),
            'resolved_at': warning.resolved_at.isoformat() if warning.resolved_at else None,
            'resolution_note': warning.resolution_note,
            'explanation': explanation,
            'treatment_logs': log_list,
        })


class WarningTreatmentView(APIView):
    permission_classes = []  # 临时禁用认证

    def post(self, request, pk):
        """处理预警"""
        try:
            warning = WarningInstance.objects.get(pk=pk)
        except WarningInstance.DoesNotExist:
            return Response(
                {'error': '预警不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get('action')
        note = request.data.get('note', '')

        if not action:
            return Response(
                {'error': 'action 是必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 处理不同的操作
        if action == 'assign':
            assignee_id = request.data.get('assignee_id')
            if assignee_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    assignee = User.objects.get(id=assignee_id)
                    warning.assignee = assignee
                    warning.save()
                except User.DoesNotExist:
                    return Response(
                        {'error': '指定的用户不存在'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        elif action == 'start':
            warning.status = 'processing'
            warning.save()

        elif action == 'resolve':
            if not note:
                return Response(
                    {'error': '解除预警必须填写处理结果'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            warning.status = 'resolved'
            warning.resolution_note = note
            warning.resolved_at = timezone.now()
            warning.save()

        elif action == 'mark_false_alarm':
            warning.status = 'false_alarm'
            warning.resolution_note = note
            warning.resolved_at = timezone.now()
            warning.save()

        elif action == 'close':
            if not note:
                return Response(
                    {'error': '关闭预警必须填写处理结果'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            warning.status = 'closed'
            warning.resolution_note = note
            warning.resolved_at = timezone.now()
            warning.save()

        elif action == 'reopen':
            warning.status = 'pending'
            warning.resolved_at = None
            warning.save()

        # 记录日志
        WarningTreatmentLog.objects.create(
            warning=warning,
            operator=request.user,
            action=action,
            note=note
        )

        return Response({
            'id': warning.id,
            'status': warning.status,
            'message': '操作成功'
        })


class WarningStatsView(APIView):
    permission_classes = []  # 临时禁用认证

    def get(self, request):
        """获取预警统计数据"""
        warnings = WarningInstance.objects.all()

        # 根据角色过滤
        if hasattr(request.user, 'role'):
            if request.user.role == 'teacher':
                warnings = warnings.filter(student__advisor_name=request.user.username)
            elif request.user.role == 'student':
                warnings = warnings.filter(student__student_id=request.user.username)

        # 按风险等级统计
        from django.db.models import Count
        risk_level_stats = warnings.values('rule__risk_level').annotate(
            count=Count('id')
        ).order_by('rule__risk_level')

        # 按状态统计
        status_stats = warnings.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        # 按规则统计
        rule_stats = warnings.values('rule__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'risk_level_stats': list(risk_level_stats),
            'status_stats': list(status_stats),
            'rule_stats': list(rule_stats),
            'total_count': warnings.count(),
        })
