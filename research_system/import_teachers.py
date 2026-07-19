import os
import django
from django.contrib.auth.hashers import make_password

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_system.settings')
django.setup()

from api.models import User, Dept

teachers_by_dept = {
    '科学社会主义系': [
        '郭春生', '蒋锐', '李宏', '李亚洲', '刘玉安', '臧秀玲', '赵婷',
        '吕连仁', '王鹏权', '金淑霞', '庞敏', '杨春林', '胡志伟'
    ],
    '政治学系': [
        '楚成亚', '方雷', '孔令栋', '李济时', '李振', '王成', '张继亮',
        '刘琳', '法帅', '王军洋', '徐会平', '钟诚',
        '党成孝', '姬生翔', '黄靖', '孔令伟', '叶紫蒙', '白江波'
    ],
    '国际政治系': [
        '李昕蕾', '黄登学', '李慧明', '刘昌明', '秦亚青', '马荣久', '盛力',
        '王学玉', '张淑兰', '朱贵昌', '方炯升', '黄栋', '展妍男', '赵均佳',
        '米雪', '王薪喜', '霍文乐'
    ],
    '公共管理系': [
        '曹现强', '韩自强', '李辉', '李延伟', '马奔', '马永驰', '楼苏萍',
        '黄晴', '孙宗锋', '滕玉成', '王佃利', '邢占军', '张乐', '张天舒',
        '韩丽华', '季丽新', '李广', '魏铭', '杨志', '王元亮', '俞少宾',
        '刘浩', '刘华兴', '费立国', '程龙', '冷安丽', '陈仁兴', '郑子君',
        '高原', '张健彬', '郑国栋', 'Yunsoo Lee',
        '李欢欢', '陈静', '褚雷', '李梦丹', '赵志华', '罗聪', '朱林旭'
    ]
}

def import_teachers():
    for dept_name, names in teachers_by_dept.items():
        dept, _ = Dept.objects.get_or_create(dept_name=dept_name)
        for name in names:
            if User.objects.filter(real_name=name).exists():
                print(f"跳过已存在教师: {name}")
                continue
            username = f"teacher_{name.replace(' ', '_')}"
            password = make_password('123456')
            User.objects.create(
                username=username,
                password=password,
                real_name=name,
                role='teacher',
                title='教授',  # 可后续调整
                dept=dept
            )
            print(f"导入教师: {name} ({dept_name})")

if __name__ == '__main__':
    import_teachers()
    print("教师导入完成！")