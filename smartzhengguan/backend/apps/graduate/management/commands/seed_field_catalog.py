"""
管理命令：初始化字段目录
"""
from django.core.management.base import BaseCommand

from apps.graduate.models import FieldCatalog


class Command(BaseCommand):
    help = "Initialize field catalog for import/export"

    def handle(self, *args, **options):
        fields = [
            # 学生基本信息
            {
                'module': 'student',
                'field_code': 'student.student_id',
                'field_name_cn': '学号',
                'data_type': 'string',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': False,
                'aliases': ['学号', 'studentid', 'student_id', '学生学号'],
                'example': '2021001001',
            },
            {
                'module': 'student',
                'field_code': 'student.name',
                'field_name_cn': '姓名',
                'data_type': 'string',
                'data_granularity': 'student',
                'is_sensitive': True,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': False,
                'aliases': ['姓名', 'name', '学生姓名'],
                'example': '张三',
            },
            {
                'module': 'student',
                'field_code': 'student.gender',
                'field_name_cn': '性别',
                'data_type': 'enum',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'dict_items': ['男', '女'],
                'aliases': ['性别', 'gender', '性别'],
                'example': '男',
            },
            {
                'module': 'student',
                'field_code': 'student.college',
                'field_name_cn': '学院',
                'data_type': 'string',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['学院', 'college', '所属学院'],
                'example': '计算机学院',
            },
            {
                'module': 'student',
                'field_code': 'student.major',
                'field_name_cn': '专业',
                'data_type': 'string',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['专业', 'major', '所学专业'],
                'example': '计算机科学与技术',
            },
            {
                'module': 'student',
                'field_code': 'student.grade',
                'field_name_cn': '年级',
                'data_type': 'string',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['年级', 'grade', '入学年级'],
                'example': '2021级',
            },
            {
                'module': 'student',
                'field_code': 'student.degree_type',
                'field_name_cn': '培养层次',
                'data_type': 'enum',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'dict_items': ['academic_master', 'professional_master', 'doctoral'],
                'aliases': ['培养层次', 'degree_type', '学位类型'],
                'example': 'academic_master',
            },
            {
                'module': 'student',
                'field_code': 'student.advisor_name',
                'field_name_cn': '导师姓名',
                'data_type': 'string',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['导师', '导师姓名', 'advisor', '指导教师'],
                'example': '李教授',
            },
            {
                'module': 'student',
                'field_code': 'student.current_status',
                'field_name_cn': '学籍状态',
                'data_type': 'enum',
                'data_granularity': 'student',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'dict_items': ['active', 'suspended', 'withdrawn', 'extended', 'other'],
                'aliases': ['学籍状态', 'status', '在读状态'],
                'example': 'active',
            },

            # 奖学金相关
            {
                'module': 'scholarship',
                'field_code': 'scholarship.award_name',
                'field_name_cn': '奖学金名称',
                'data_type': 'string',
                'data_granularity': 'event',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': False,
                'aliases': ['奖学金名称', 'award', '奖项名称'],
                'example': '国家奖学金',
            },
            {
                'module': 'scholarship',
                'field_code': 'scholarship.amount',
                'field_name_cn': '奖学金金额',
                'data_type': 'decimal',
                'data_granularity': 'event',
                'is_sensitive': False,
                'is_filterable': False,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['金额', 'amount', '奖励金额'],
                'example': '20000',
            },
            {
                'module': 'scholarship',
                'field_code': 'scholarship.award_year',
                'field_name_cn': '获奖年度',
                'data_type': 'integer',
                'data_granularity': 'event',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': False,
                'aliases': ['获奖年度', 'year', '年度'],
                'example': '2023',
            },

            # 就业相关
            {
                'module': 'employment',
                'field_code': 'employment.employer_name',
                'field_name_cn': '就业单位',
                'data_type': 'string',
                'data_granularity': 'event',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': False,
                'aliases': ['就业单位', 'employer', '单位名称'],
                'example': '华为技术有限公司',
            },
            {
                'module': 'employment',
                'field_code': 'employment.destination_type',
                'field_name_cn': '去向类型',
                'data_type': 'string',
                'data_granularity': 'event',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['去向类型', 'destination', '就业类型'],
                'example': '企业就业',
            },
            {
                'module': 'employment',
                'field_code': 'employment.province',
                'field_name_cn': '就业省份',
                'data_type': 'string',
                'data_granularity': 'event',
                'is_sensitive': False,
                'is_filterable': True,
                'is_exportable': True,
                'is_aggregatable': True,
                'aliases': ['省份', 'province', '就业地区'],
                'example': '广东省',
            },
        ]

        created_count = 0
        updated_count = 0

        for field_data in fields:
            field_code = field_data['field_code']
            obj, created = FieldCatalog.objects.update_or_create(
                field_code=field_code,
                defaults=field_data
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Field catalog seeded: {created_count} created, {updated_count} updated'
            )
        )
