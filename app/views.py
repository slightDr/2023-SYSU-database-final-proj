# 【url执行的函数，重要】
from django.shortcuts import HttpResponse, render, redirect
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
import psycopg2
import random
from django import forms
from datetime import datetime
import json
import re

db_host = '192.168.42.129'
db_port = '5432'
db_name = 'postgres'
curr_id = 10000000
key_map = {'customers': 'c_id', 'managers': 'm_id', 'bus': 'b_plate', 'orders': 'o_id', 'route': 'r_id',
           'schedule': 's_id'}


def is_password_complex(password):
    # 至少包含一个大写字母
    if not re.search(r'[A-Z]', password):
        return False

    # 至少包含一个小写字母
    if not re.search(r'[a-z]', password):
        return False

    # 至少包含一个数字
    if not re.search(r'\d', password):
        return False

    # 至少包含一个特殊字符
    if not re.search(r'[!@#$%^&*_]', password):
        return False

    # 密码长度至少为5个字符
    if len(password) < 5:
        return False

    return True


def search_all(table_name):
    """
    查找整个表
    :param table_name: 查找的表名
    :return: 字典的列表[{col1: val1, col2: val2...}, {...}, ...]，每个字典代表一行
    """
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()

    # 获取整个表的值
    cursor.execute("select * from " + table_name)
    res = []
    tmp = cursor.fetchall()  # 数据的真实数值的元组组成的列表[(), (), ...]，一个元组一行
    conn.commit()

    # 获取每个属性名
    cursor.execute("select column_name from information_schema.columns  \
                    where table_schema='public' and table_name='" + table_name + "';")
    tmp_idx = cursor.fetchall()  # 数据的属性名的元组组成的列表[('m_id',), ('m_name',), ('m_pwd',)]
    conn.commit()

    conn.close()

    # 处理数据格式
    for i in range(len(tmp)):
        res.append({})
        for j in range(len(tmp[i])):
            res[i][tmp_idx[j][0]] = tmp[i][j]

    return res  # [{val1: key1, ...}, {}, ...]


def search_cond(table_name, key):
    """
    根据primary_key的值key搜索table_name对应行
    :param table_name: 列表名
    :param key: primary key的值
    :return: 返回 table_name 表中主键值 = key的那一行的字典 {key1: val1, key2: val2, ...}
    """
    all_items = search_all(table_name)  # [{key1: val1,...}, {}, ...]
    key_name = key_map[table_name]  # 找到对应的key名
    for item in all_items:  # 遍历每一行的字典
        if item[key_name] == key:  # 主键值相等
            return item  # 返回该行的字典 {key1: val1, key2: val2, ...}
    return None


def insert_to_table(table_name, values: list):
    """
    在table_name表中插入values
    :param table_name: 插入的表名
    :param values: 插入的值列表
    :return: [True, ""]: 插入成功;
             [False, "<失败原因>"]： 插入失败
    """
    n = len(values)
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()

    # 获取元素类型
    cursor.execute(f"SELECT data_type \
                     FROM information_schema.columns \
                     WHERE table_schema = 'public' AND table_name = '{table_name}';")
    types = cursor.fetchall()

    # 根据values和types综合处理出INSERT语句
    insert = f"INSERT INTO {table_name} VALUES("
    for i in range(n):
        value, d_type = values[i], types[i][0]
        if d_type == 'integer' or d_type == 'float':
            if i < n - 1:
                insert += f"{value}, "
            else:
                insert += f"{value});"
        else:
            if i < n - 1:
                insert += f"'{value}', "
            else:
                insert += f"'{value}');"
    flag = True
    news = ""
    # 尝试执行INSERT语句
    try:
        cursor.execute(insert)  # 尝试执行
    except psycopg2.Error as e:
        flag = False
        news = e

    conn.commit()
    conn.close()
    return [flag, news]


def update_record(table_name, column_name, val, key_val):
    """
    根据primary key的值key_val更新语句
    :param table_name: 修改的表名
    :param column_name: 修改的列名
    :param val: 修改的值
    :param key_val: 想要修改的那一行的primary key的值
    :return:
        成功: [True, 1]
        没有该column_name: [False, 2]
        val不合法: [False, ”<不合法原因>“]
    """
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name, data_type \
                     FROM information_schema.columns \
                     WHERE table_schema = 'public' AND table_name = '{table_name}';")
    # 获取主键名 key_name, 主键类型 key_type, column_name 类型 d_type
    tmp = cursor.fetchall()
    n = len(tmp)
    key_name, key_type, d_type = tmp[0][0], tmp[0][1], ""
    for i in range(n):
        if column_name == tmp[i][0]:
            d_type = tmp[i][1]
            break
    if d_type == "":
        return [False, "2"]
    # 编写更新语句
    query = f"UPDATE {table_name} SET {column_name} = "
    if d_type == "integer" or d_type == "float":
        query += f"{val} "
    else:
        query += f"'{val}' "
    query += f"WHERE {key_name} = "
    if key_type == "integer" or key_type == "float":
        query += f"{key_val};"
    else:
        query += f"'{key_val}';"
    print(query)

    try:  # 尝试执行
        cursor.execute(query)
    except psycopg2.Error as e:
        return [False, e]

    conn.commit()
    conn.close()
    return [True, "1"]


def delete_record(table_name, key_val):
    """
    根据primary key的值执行删除语句
    :param table_name: 删除的表名
    :param key_val: 删除的项的主键值
    :return: none
    """
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name, data_type \
                     FROM information_schema.columns \
                     WHERE table_schema = 'public' AND table_name = '{table_name}';")
    tmp = cursor.fetchall()
    # 获取主键的名字和数据类型
    key_name, key_type = tmp[0][0], tmp[0][1]

    # 执行删除
    if key_type == 'integer' or key_type == 'float':
        cursor.execute(f"DELETE FROM {table_name} \
                         WHERE {key_name} = {key_val};")
    else:
        cursor.execute(f"DELETE FROM {table_name} \
                         WHERE {key_name} = '{key_val}';")

    conn.commit()
    conn.close()


def delete_cond(table_name, column_name, column_val):
    """
    根据column_name的值column_val在table_name表中删除对应行。
    :param table_name: 删除操作的表名
    :param column_name: 想要查找的列名
    :param column_val: 列名对应的列值
    :return: none
    """
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()
    # 编写delete语句
    command = ""
    if isinstance(column_val, str):
        command = f"DELETE FROM {table_name} WHERE {column_name}='{column_val}'"
    else:
        command = f"DELETE FROM {table_name} WHERE {column_name}={column_val}"
    print(command)
    # 执行语句
    cursor.execute(command)
    conn.close()


# 1
def register(request):
    form = ['', '', '', '', '']
    sure_pwd = ''
    if request.method == 'GET':
        return render(request, 'register.html', {'form': form, 'sure': sure_pwd})

    post = request.POST
    # request.POST = [c_id, c_name, c_pwd, sure_pwd, c_tel, c_tors]
    print(f"身份为{post.get('c_tors')}")
    form[0] = int(post.get('c_id'))
    form[1] = post.get('c_name')
    form[2] = post.get('c_pwd')
    sure_pwd = post.get('confirm')
    form[3] = post.get('c_tel')
    form[4] = 1 if post.get('c_tors') == 'teacher' else 0

    if form[0] < 10000000 or form[0] > 99999999:
        form[0] = ''
        return render(request, 'register.html', {'form': form, 'sure': sure_pwd, 'err_msg': "学工号需为8位"})
    elif not is_password_complex(form[2]):
        form[2] = sure_pwd = ''
        return render(request, 'register.html', {'form': form, 'sure': sure_pwd, 'err_msg': "密码复杂度不足，至少包含大小写字母和特殊符号，长度至少为5"})
    elif form[2] != sure_pwd:
        form[2] = sure_pwd = ''
        return render(request, 'register.html', {'form': form, 'sure': sure_pwd, 'err_msg': "确认密码需与密码一致"})

    [flag, err] = insert_to_table("customers", form)
    if flag is not True:
        form = ['', '', '', '', '']
        return render(request, 'register.html', {'form': form, 'err_msg': err})
    return redirect("/login/")


# 2
def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    # return redirect('/user/?c_id=21307251&c_name=叶鸿彬')
    form = ['', '']
    post = request.POST
    form[0] = post.get("c_id")
    form[1] = request.POST.get("c_pwd")
    try:
        form[0] = int(form[0])
    except ValueError:
        form[0] = ''
        return render(request, 'login.html', {'form': form, 'err_msg': '学工号需为数字'})
    # 查找user中的账号
    cus = search_all('customers')
    for c in cus:
        c_id, c_pwd, c_name = c['c_id'], c['c_pwd'], c['c_name']
        if c_id == form[0]:
            if c_pwd == form[1]:  # 账号对上了且密码正确
                global curr_id
                curr_id = c_id
                return redirect(f'/user/?c_id={c_id}&c_name={c_name}')
            form[1] = ''
            return render(request, 'login.html', {'form': form, 'err_msg': '密码错误'})  # 账号对密码错
    print("查找完user")
    # 查找manager中的账号
    mans = search_all('managers')
    for m in mans:
        m_id, m_pwd, m_name = m['m_id'], m['m_pwd'], m['m_name']
        if m_id == form[0]:
            if m_pwd == form[1]:  # 账号对上了且密码正确
                return redirect(f'/manager/?m_id={m_id}&m_name={m_name}')
            form[1] = ''
            return render(request, 'login.html', {'form': form, 'err_msg': '密码错误'})  # 账号对密码错

    form = ['', '']
    return render(request, 'login.html', {'form': form, 'err_msg': '账号未注册'})


# 17
def reset_pwd(request):
    if request.method == 'GET':
        return render(request, 'reset_pwd.html')

    post = request.POST
    account = int(post.get('account'))
    new_pwd = post.get('newpwd')
    confirm = post.get('confirm')
    tel = post.get('tel')
    print(account, new_pwd, confirm, tel)
    if not is_password_complex(new_pwd):
        return render(request, 'reset_pwd.html', {'err_msg': '密码复杂度不足，至少有一个大写字母，一个小写字母，一个特殊符号，长度不少于5',
                                                  'c_id': account, 'c_tel': tel})
    elif new_pwd != confirm:
        return render(request, 'reset_pwd.html', {'err_msg': '确认密码需与新密码一致',
                                                  'c_id': account, 'c_tel': tel})
    info = search_cond('customers', account)
    real_tel = info['c_tel']
    print(real_tel, tel)
    if real_tel != tel:
        return render(request, 'reset_pwd.html', {'err_msg': '手机号验证不一致',
                                                  'c_id': account, 'c_tel': tel, 'c_pwd': new_pwd})
    result = update_record('customers', 'c_pwd', new_pwd, account)
    print(result)
    return redirect('/login/')


# 3
def user(request):
    if request.method == 'GET':
        c_id, c_name = request.GET.get('c_id'), request.GET.get('c_name')
        current_date = datetime.now().strftime('%Y-%m-%d')
        return render(request, "user.html", {'id': c_id, 'name': c_name, 'date': current_date})
    # print(request.method)
    # 获取参数
    # global latest
    c_id, c_name = request.GET.get('c_id'), request.GET.get('c_name')
    current_date = datetime.now().strftime('%Y-%m-%d')
    s_id = int(request.GET.get('s_id'))
    price = float(request.GET.get('price'))
    role = search_cond('customers', int(c_id))['c_tors']
    discount = 0.8 if role == 1 else 1.0
    new_price = price * (0.8 if role == 1 else 1)
    # print(role, discount, price, new_price)
    status = 1
    managers = search_all('managers')
    m_id = random.choice(managers)['m_id']
    # print(c_id, c_name, current_date, s_id)
    # 插入orders
    while True:
        latest = random.randint(100000001, 200000000)
        result = insert_to_table('orders', [latest, new_price, discount, status, s_id, c_id, m_id])
        if result[0]:
            new_remain = search_cond('schedule', int(s_id))['remain'] - 1
            update_record('schedule', 'remain', new_remain, int(s_id))
            break
    return render(request, "user.html", {'id': c_id, 'name': c_name, 'date': current_date})


# 4
def user_info(request):
    c_id, c_name = int(request.GET.get('c_id')), request.GET.get('c_name')
    # 查找 c_id 记录
    find = search_cond('customers', c_id)
    if not find:
        return
    print(find)
    c_tel, c_pwd, c_tors = find['c_tel'], find['c_pwd'], find['c_tors']
    role = '老师' if c_tors == 1 else '学生'
    # 更新的参数form，更新的键名key_name
    form = [c_name, c_tel, c_pwd, c_pwd]
    key_name = ['c_name', 'c_tel', 'c_pwd']
    # c_tel = '13560114161'
    # c_pwd = '123'
    # role = '学生'
    if request.method == 'GET':
        return render(request, "info.html", {'id': c_id, 'name': c_name, 'form': form, 'role': role})

    post = request.POST
    # form分别为 new_name, new_tel, new_pwd, confirm_pwd
    form[0], form[1], form[2], form[3] = post.get('c_name'), post.get('c_tel'), post.get('c_pwd'), \
                                         post.get('confirm_pwd')
    # 检查新信息的合法性
    if len(form[2]) < 5:
        form[2] = form[3] = ''
        return render(request, "info.html", {'id': c_id, 'form': form, 'role': role, 'err_msg': '密码长度至少为5'})
    elif form[2] != form[3]:
        form[2] = form[3] = ''
        return render(request, "info.html", {'id': c_id, 'form': form, 'role': role, 'err_msg': '确认密码与密码不一致'})
    # 更新信息
    for i in range(3):
        update_record('customers', key_name[i], form[i], c_id)

    return redirect(f'/user/?c_id={c_id}&c_name={form[0]}')


# 7
def user_account(request):
    print(request.method)
    if request.method == 'GET':
        c_id, c_name = int(request.GET.get('c_id')), request.GET.get('c_name')
        # print(c_id, type(c_id))
        orders = search_all('orders')
        my_order = []
        # 把需要的信息放进 my_order 中
        for order in orders:
            # print(type(order['c_id']))
            if c_id == order['c_id']:
                tmp_list = []
                tmp_list.append('支付成功' if order['status'] == 1 else '已退款')
                tmp_list.append(order['o_id'])
                schedule = search_cond('schedule', int(order['s_id']))
                tmp_list.append(schedule['b_plate'])
                r_id = schedule['r_id']
                route = search_cond('route', int(r_id))
                tmp_list.append(route['s_time'])
                tmp_list.append(route['e_time'])
                tmp_list.append(route['s_pos'])
                tmp_list.append(route['e_pos'])
                tmp_list.append('八折' if order['discount'] == 0.8 else '无')
                tmp_list.append(order['o_price'])
                my_order.append(tmp_list)
        print(my_order)
        return render(request, "account.html", {'list': my_order, 'id': c_id, 'name': c_name})

    # 退票
    c_id, c_name = int(request.GET.get('c_id')), request.GET.get('c_name')
    o_id = int(request.GET.get('o_id'))
    update_record('orders', 'status', 0, o_id)  # 更新订单状态
    order = search_cond('orders', o_id)
    s_id = int(order['s_id'])
    remain = int(search_cond('schedule', s_id)['remain'])
    update_record('schedule', 'remain', remain + 1, s_id)  # 更新route的余票
    orders = search_all('orders')
    my_order = []
    # 把需要的信息放进 my_order 中
    for order in orders:
        # print(type(order['c_id']))
        if c_id == order['c_id']:
            tmp_list = []
            tmp_list.append('支付成功' if order['status'] == 1 else '已退款')
            tmp_list.append(order['o_id'])
            schedule = search_cond('schedule', int(order['s_id']))
            tmp_list.append(schedule['b_plate'])
            r_id = schedule['r_id']
            route = search_cond('route', int(r_id))
            tmp_list.append(route['s_time'])
            tmp_list.append(route['e_time'])
            tmp_list.append(route['s_pos'])
            tmp_list.append(route['e_pos'])
            tmp_list.append('八折' if order['discount'] == 0.8 else '无')
            tmp_list.append(order['o_price'])
            my_order.append(tmp_list)
    print(my_order)
    return render(request, "account.html", {'list': my_order, 'id': c_id, 'name': c_name})


# 5
def search_route(request):
    # if request.method == 'GET':
    info = request.GET
    print(info)
    src, dest, time = info.get('departure'), info.get('destination'), info.get('departure-date')
    c_id, c_name = info.get('c_id'), info.get('c_name')
    # print(type(src), dest, type(time))
    if src == dest:
        return render(request, "user.html", {'id': c_id, 'name': c_name, 'err_msg': '起始站和目的地不可以相同'})
    elif time == '':
        return render(request, "user.html", {'id': c_id, 'name': c_name, 'err_msg': '请选择时间'})

    # all_schedule = search_all('schedule')
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()
    # 搜索符合要求的班次
    cursor.execute(f"SELECT * FROM schedule \
                        JOIN route ON schedule.r_id = route.r_id \
                        JOIN bus ON schedule.b_plate = bus.b_plate \
                     WHERE s_pos = '{src}' AND e_pos = '{dest}' AND s_time LIKE '{time}%';")
    # result=[s_id, b_plate, r_id, remain, r_id, s_time, e_time, s_pos, e_pos, b_plate, b_model, b_cap]
    result = cursor.fetchall()
    # print(result)
    conn.close()
    # 放入所需信息
    search_list = []
    prices = {'大巴': 40.0, '中巴': 80.0, '小巴': 100.0}
    print(type(prices['大巴']))
    for schedule in result:
        schedule = list(schedule)
        schedule[5] = datetime.strptime(schedule[5], "%Y-%m-%d %H:%M")
        schedule[6] = datetime.strptime(schedule[6], "%Y-%m-%d %H:%M")
        search_list.append([schedule[0], schedule[5], schedule[6], schedule[7], schedule[8], schedule[3], schedule[10],
                            prices[schedule[10]]])
    return render(request, "search_route.html", {'list': search_list, 'id': c_id, 'name': c_name})


# 6
def buy(request):
    info = request.GET
    form = ['', '', '', '', '', '', '', '']
    s_id = int(info.get('s_id'))
    c_id, c_name = info.get('c_id'), info.get('c_name')
    # 检查该客户是否已经购买过该票
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM orders \
                     WHERE c_id = {c_id} AND s_id = {s_id}")
    content = cursor.fetchall()
    # print(type(content[0][3]))
    # print(content)
    flag = False
    for i in range(len(content)):  # 看看该客户购买的该路线的票是否有一张未退款
        if content[i][3] == 1:
            flag = True
            break
    if len(content) > 0 and flag:  # 如果搜到了记录
        return render(request, "user.html", {'id': c_id, 'name': c_name, 'err_msg': '您已购买过该班次'})

    schedule = search_cond('schedule', s_id)
    # form=[b_plate, s_time, e_time, s_pos, e_pos, price, remain]
    form[0] = schedule['b_plate']
    form[1], form[2] = info.get('s_time'), info.get('e_time')
    # 把s_time的a.m.或p.m.替换成am或pm
    form[1] = form[1].replace('a.m.', 'am')
    form[1] = form[1].replace('p.m.', 'pm')
    form[1] = form[1].replace('noon', '12 pm')
    # 把e_time的a.m.或p.m.替换成am或pm
    form[2] = form[2].replace('a.m.', 'am')
    form[2] = form[2].replace('p.m.', 'pm')
    form[2] = form[2].replace('noon', '12 pm')
    # 把s_time和e_time转换成时间格式
    form[1] = datetime.strptime(form[1], "%b. %d, %Y, %I %p")
    form[2] = datetime.strptime(form[2], "%b. %d, %Y, %I %p")
    # print(form[1])
    # print(form[2])
    form[3], form[4], form[5], form[6] = info.get('s_pos'), info.get('e_pos'), info.get('price'), info.get('remain')
    form[7] = s_id
    # print(form)
    return render(request, "buy.html", {'form': form, 'id': c_id, 'name': c_name})


# 8
def manager(request):
    m_id, m_name = request.GET.get('m_id'), request.GET.get('m_name')
    return render(request, "manager.html", {'id': m_id, 'name': m_name})


# 9
def manager_info(request):
    m_id, m_name = int(request.GET.get('m_id')), request.GET.get('m_name')
    print(m_id, type(m_id))
    # 查找 c_id 记录
    find = search_cond('managers', m_id)
    if not find:
        return
    print(find)
    m_pwd = find['m_pwd']
    # 更新的参数form，更新的键名key_name
    form = [m_name, m_pwd, m_pwd]
    # print(f"修改前{form}")
    key_name = ['m_name', 'm_pwd']

    if request.method == 'GET':
        return render(request, "manager_info.html", {'id': m_id, 'name': m_name, 'form': form})

    post = request.POST
    # form分别为 new_name, new_tel, new_pwd, confirm_pwd
    form[0], form[1], form[2] = post.get('c_name'), post.get('c_pwd'), post.get('confirm_pwd')
    # print(f"修改后{form}")
    # 检查新信息的合法性
    if len(form[1]) < 5:
        form[1] = form[2] = ''
        return render(request, "manager_info.html", {'id': m_id, 'form': form, 'err_msg': '密码长度至少为5'})
    elif form[1] != form[1]:
        form[1] = form[2] = ''
        return render(request, "manager_info.html", {'id': m_id, 'form': form, 'err_msg': '确认密码与密码不一致'})
    # 更新信息
    for i in range(2):
        update_record('managers', key_name[i], form[i], m_id)

    return redirect(f'/manager/?m_id={m_id}&m_name={form[0]}')


# 10
def manage_user(request):
    m_id, m_name = request.GET.get('m_id'), request.GET.get('m_name')
    delete_id = request.GET.get('delete_id')
    if delete_id:
        delete_id = int(delete_id)
        print(delete_id, type(delete_id))
        # delete_cond('orders', 'c_id', delete_id)
        delete_record('customers', delete_id)
    all_cus = search_all('customers')
    cus_list = []
    for cus in all_cus:
        tmp = [cus['c_id'], cus['c_name'], cus['c_pwd'], cus['c_tel'], ('学生' if cus['c_tors'] == 0 else '老师')]
        # print(tmp)
        cus_list.append(tmp)
    # print(cus_list)
    return render(request, "manage_user.html", {'list': cus_list, 'id': m_id, 'name': m_name})


# 11
def manage_add_user(request):
    m_id, m_name = request.GET.get('m_id'), request.GET.get('m_name')
    if request.method == 'GET':
        return render(request, "manage_add_user.html", {'id': m_id, 'name': m_name})
    post = request.POST
    form = [0, '', '', '', '']
    form[0] = int(post.get('c_id'))
    form[1] = post.get('c_name')
    form[2] = post.get('c_pwd')
    form[3] = post.get('c_tel')
    print(post.get('c_tors'))
    form[4] = (0 if post.get('c_tors') == 'student' else 1)
    print(form)
    result = insert_to_table('customers', form)
    print(result)
    return redirect(f'/manager/manage_user/?m_id={m_id}&m_name={m_name}')


# 14
def modify_user(request):
    if request.method == 'POST':
        data = request.POST
        print(data, type(data))
        # 获取 JSON 格式的字符串
        form = list(data.keys())[0]
        # 解析 JSON 数据
        form = json.loads(form)
        # print(form)
        form[0] = int(form[0])
        form[4] = int(form[4] == '老师')
        print(form)
        result = list()
        result.append(update_record('customers', 'c_name', form[1], form[0]))
        result.append(update_record('customers', 'c_pwd', form[2], form[0]))
        result.append(update_record('customers', 'c_tel', form[3], form[0]))
        result.append(update_record('customers', 'c_tors', form[4], form[0]))
        print(result)
        return JsonResponse({'message': '数据已成功更新'})
    else:
        return JsonResponse({'message': '请求方法不支持'})


# 12
def manage_order(request):
    m_id, m_name = request.GET.get('m_id'), request.GET.get('m_name')
    del_id = request.GET.get('delete_id')
    if request.method == 'GET':
        m_id = int(m_id)
        if del_id:
            del_id = int(del_id)
            print(del_id)
            delete_record('orders', del_id)

        conn = psycopg2.connect(database=db_name,
                                user='yhb',
                                password='Bennyyip_0915',
                                host=db_host,
                                port=db_port)
        # 创建cursor对象：
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM orders JOIN schedule ON orders.s_id = schedule.s_id")
        orders = cursor.fetchall()
        conn.close()

        o_list = []
        for order in orders:
            # print(order)
            route = search_cond('route', order[9])
            # print(route)

            # append[o_id, c_id, 起点, 终点, 起始时间,
            # b_plate, 价格, 状态]
            o_list.append([order[0], order[5], route['s_pos'], route['e_pos'], route['s_time'],
                           order[8], order[1], ("已退款" if order[3] == 0 else "已支付")])
        print(o_list)
        return render(request, "manage_order.html", {'list': o_list, 'id': m_id, 'name': m_name})


# 15
def modify_order(request):
    if request.method == 'POST':
        data = request.POST
        # print(data, type(data))
        # 获取 JSON 格式的字符串
        form = list(data.keys())[0]
        # 解析 JSON 数据
        form = json.loads(form)
        # print(form)
        form[0] = int(form[0])
        form[1] = int(form[1] == '已支付')
        order = search_cond('orders', form[0])
        old_status = int(order.get('status'))
        # s_id = int(order.get('s_id'))
        if old_status == form[1]:
            print("未改变")
        else:
            print(f"原状态{old_status}, 现状态{form[1]}")
            result = list()
            result.append(update_record('orders', 'status', form[1], form[0]))
            s_id = int(order.get('s_id'))
            remain = int(search_cond('schedule', s_id).get('remain'))
            new_rem = (remain - 1) if form[1] == 1 else (remain + 1)
            print(f"原余座{remain}, 现余座{new_rem}")
            result.append(update_record('schedule', 'remain', new_rem, s_id))
            print(result)
        return JsonResponse({'message': '数据已成功更新'})
    else:
        return JsonResponse({'message': '请求方法不支持'})


# 13
def manage_sche(request):
    m_id, m_name = request.GET.get('m_id'), request.GET.get('m_name')
    del_id = request.GET.get('delete_id')
    if del_id:
        del_id = int(del_id)
        delete_record('schedule', del_id)
    conn = psycopg2.connect(database=db_name,
                            user='yhb',
                            password='Bennyyip_0915',
                            host=db_host,
                            port=db_port)
    # 创建cursor对象：
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM schedule, route WHERE schedule.r_id = route.r_id")
    schedule = cursor.fetchall()
    conn.close()

    s_list = []
    for s in schedule:
        print(s)
        # append[s_id, s_pos, e_pos, s_time, b_plate, remain]
        s_list.append([s[0], s[7], s[8], s[5], s[1], s[3]])
    return render(request, "manage_sche.html", {'list': s_list, 'id': m_id, 'name': m_name})


# 16
def modify_sche(request):
    if request.method == 'POST':
        data = request.POST
        # print(data, type(data))
        # 获取 JSON 格式的字符串
        form = list(data.keys())[0]
        # 解析 JSON 数据
        form = json.loads(form)
        print(form)
        form[0] = int(form[0])
        form[1] = int(form[1])
        result = update_record('schedule', 'remain', form[1], form[0])
        print(result)
        return JsonResponse({'message': '数据已成功更新'})
    else:
        return JsonResponse({'message': '请求方法不支持'})


# info = request.POST
# s_id = int(info.get('s_id'))
# print(s_id)
# return render(request, "buy.html")


# pos = ['南校', '东校', '北校', '珠海校区', '深圳校区']
# date = ['2023-10-24', '2023-10-25']
# s_time = ['08:00', '10:00', '13:00', '15:00', '18:00', '20:00']
# e_time = ['10:00', '12:00', '15:00', '17:00', '20:00', '22:00']
# start = 100000001
# for i in range(5):
#     for j in range(5):
#         if i != j:
#             for k in range(6):
#                 s_t = date[0] + ' ' + s_time[k]
#                 e_t = date[0] + ' ' + e_time[k]
#                 insert_to_table('route', [start, s_t, e_t, pos[i], pos[j]])
#                 start += 1
#                 s_t = date[1] + ' ' + s_time[k]
#                 e_t = date[1] + ' ' + e_time[k]
#                 insert_to_table('route', [start, s_t, e_t, pos[i], pos[j]])
#                 start += 1


# # 定义大巴的型号和容量
# bus_models = ['大巴', '中巴', '小巴']
# bus_capacities = {'大巴': 50, '中巴': 20, '小巴': 16}
#
#
# # 生成车牌号码的函数
# def generate_license_plate():
#     # province = random.choice(['粤', '京', '沪', '津', '浙', '苏', '鲁', '豫', '川', '渝'])  # 随机选择省份
#     # letters = ''.join([chr(random.randint(65, 90)) for _ in range(2)])  # 生成2个随机大写字母
#     numbers = ''.join([str(random.randint(0, 9)) for _ in range(5)])  # 生成5个随机数字
#     return "粤A" + numbers  # 拼接成车牌号
#
#
# for _ in range(200):
#     model = random.choice(bus_models)  # 随机选择型号
#     capacity = bus_capacities[model]  # 获取型号对应的容量
#     plate = generate_license_plate()  # 生成随机车牌号
#     insert_to_table('bus', [plate, model, capacity])


# routes = search_all('route')
# buses = search_all('bus')
# # print(len(buses))
# start = 1
# for route in routes:
#     b_choice = random.randint(0, len(buses) - 1)
#     bus = buses[b_choice]
#     insert_to_table('schedule', [start, bus.get('b_plate'), route.get('r_id'), bus.get('b_cap')])
#     start += 1
