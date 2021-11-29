import sqlite3

path_to_db = 'data_base/budget.db'

__connection = None


def get_connection():
    """Функция устанавливает соединение с базой данных"""
    global __connection
    if __connection is None:
        __connection = sqlite3.connect(path_to_db, check_same_thread=False)

    return __connection


def init_bd_users(force: bool = False):
    """Функция создает таблицу users в базе данных, если ее еще нет"""
    db = get_connection()
    cursor = db.cursor()

    if force:
        cursor.execute('DROP TABLE IF EXISTS users')

    query = """ CREATE TABLE IF NOT EXISTS users( 
    name TEXT,
    amount INTEGER,
    chat_id INTEGER
    )"""

    cursor.execute(query)
    db.commit()
    cursor.close()


def init_bd_costs(force: bool = False):
    """Функция создает таблицу costs в базе данных, если ее еще нет"""
    db = get_connection()
    cursor = db.cursor()

    if force:
        cursor.execute('DROP TABLE IF EXISTS costs')

    query = """ CREATE TABLE IF NOT EXISTS costs( 
    chat_id INTEGER,
    food INTEGER,
    taxes INTEGER,
    fun INTEGER,
    education INTEGER,
    utilities INTEGER
    )"""

    cursor.execute(query)
    db.commit()
    cursor.close()


def init_bd_vk_groups(force: bool = False):
    """Функция создает таблицу groups в базе данных, если ее еще нет"""
    db = get_connection()
    cursor = db.cursor()

    if force:
        cursor.execute('DROP TABLE IF EXISTS groups')

    query = """ CREATE TABLE IF NOT EXISTS groups( 
       person_id INTEGER,
       group_id INTEGER,
       group_name TEXT
       )"""

    cursor.execute(query)
    db.commit()


def init_bd_last_posts(force: bool = False):
    """Функция создает таблицу posts в базе данных, если её еще нет"""
    db = get_connection()
    cursor = db.cursor()

    if force:
        cursor.execute('DROP TABLE IF EXISTS posts')

    query = """ CREATE TABLE IF NOT EXISTS posts( 
           group_id INTEGER,
           post_id INTEGER
           )"""

    cursor.execute(query)
    db.commit()


def add_users(name: str = None, amount: int = None, chat_id: int = None):
    """Функция добавляет новые значения в таблицу users и costs"""
    not_have = []
    if name is None:
        not_have.append('name')
    if amount is None:
        not_have.append('amount')
    if chat_id is None:
        not_have.append('chat_id')

    for not_given in not_have:
        if not_given:
            return False, not_have

    db = get_connection()

    db.execute(""" INSERT INTO users(name, amount, chat_id) 
                    VALUES(?, ?, ?)""", (name, amount, chat_id))
    db.execute(""" INSERT INTO costs(chat_id, food, taxes, fun, education, utilities) 
                        VALUES(?, ?, ?, ?, ?, ?)""", (chat_id, 0, 0, 0, 0, 0))

    db.commit()
    return True, []


def get_profile(chat_id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("""
    SELECT name, amount, chat_id FROM users WHERE chat_id=?
    """, (chat_id,))

    profile = cursor.fetchall()
    db.commit()
    cursor.close()

    if len(profile) == 0:
        return False, []
    else:
        return True, profile


def change_data_in_profile(chat_id, data_type, replacement):
    db = get_connection()
    cursor = db.cursor()

    sql = f"""
    UPDATE users 
    SET {data_type} = '{replacement}'
    WHERE users.chat_id = '{chat_id} ' 
    """

    cursor.execute(sql)
    db.commit()
    cursor.close()
    return True


def change_data_in_costs(chat_id, data_type, replacement):
    db = get_connection()
    cursor = db.cursor()

    sql = f"""
    UPDATE costs 
    SET {data_type} = '{replacement}'
    WHERE costs.chat_id = '{chat_id} ' 
    """

    cursor.execute(sql)
    db.commit()
    cursor.close()
    return True


def get_all_expenses(chat_id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT food, taxes, fun, education, utilities FROM costs WHERE chat_id=?
        """, (chat_id,))

    profile = cursor.fetchall()
    db.commit()
    cursor.close()

    if len(profile) == 0:
        return False, []
    else:
        return True, profile


def get_all_chat_ids():
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT chat_id FROM users
        """)

    list_chat_ids = [chat_id_empty[0] for chat_id_empty in cursor.fetchall()]
    db.commit()
    cursor.close()

    return list_chat_ids


def add_group(person_id, group_id, group_name):
    db = get_connection()

    db.execute(""" INSERT INTO groups(person_id, group_id, group_name) 
                        VALUES(?, ?, ?)""", (person_id, group_id, group_name))
    db.commit()


def is_persons_group(person_id, group_id: int = None, group_name: str = None):
    groups = get_persons_groups(person_id)

    if group_name:
        for group_description in groups:
            if group_description[1] == group_name:
                return True, group_description[1]
    elif group_id:
        for group_description in groups:
            if group_description[0] == group_id:
                return True, group_description[1]
    return False, ''


def delete_group(person_id, group_id: int = None, group_name: str = None):
    db = get_connection()

    if group_name:
        db.execute(f""" DELETE FROM groups
                            WHERE person_id = {person_id} AND group_name = {"'" + group_name + "'"}""")
    elif group_id:
        db.execute(f""" DELETE FROM groups
                                    WHERE person_id = {person_id} AND group_id = {group_id}""")

    db.commit()


def get_persons_groups(person_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(f"""
        SELECT group_id, group_name FROM groups
        WHERE person_id = {person_id}
        ORDER BY group_name
        """)
    list_of_group_names = cursor.fetchall()
    cursor.close()
    return list_of_group_names


def is_new_group(group_id):
    last_post_id = get_last_post_id(group_id)

    if last_post_id:
        return False

    return True


def add_new_post(group_id, post_id):
    db = get_connection()

    db.execute(""" INSERT INTO posts(group_id, post_id) 
                            VALUES(?, ?)""", (group_id, post_id))
    db.commit()


def delete_post(group_id):
    db = get_connection()

    db.execute(f""" DELETE FROM posts
                                WHERE group_id = {group_id}""")

    db.commit()


def get_all_groups():
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(f"""
            SELECT group_id, post_id FROM posts
            """)
    list_of_group_names = cursor.fetchall()
    cursor.close()
    return list_of_group_names


def get_last_post_id(group_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(f"""
                SELECT post_id FROM posts
                WHERE group_id = {group_id}
                """)
    last_post_id = cursor.fetchall()
    cursor.close()
    if last_post_id:
        return last_post_id[0][0]
    return last_post_id


def update_last_post_id(group_id, post_id):
    db = get_connection()
    cursor = db.cursor()

    sql = f"""
        UPDATE posts 
        SET post_id = '{post_id}'
        WHERE group_id = '{group_id} ' 
        """

    cursor.execute(sql)
    db.commit()
    cursor.close()


if __name__ == '__main__':
    init_bd_users()
    init_bd_costs()
    init_bd_vk_groups()
    init_bd_last_posts()
