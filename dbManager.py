import sqlite3
import os
import pandas as pd
import json
import datetime
from utils import date_to_seconds, seconds_to_date


class DBManager:
    def __init__(self, db_path, db_filename, db_filepath, db_max_page_result):
        self.db_path = db_path
        self.db_filename = db_filename
        self.db_filepath = db_filepath
        self.db_max_page_result = db_max_page_result

    # ___
    # 初始化
    def db_main_initialize(self):
        print("——初始化数据库中……")
        conn_check = self.db_check_exist()
        self.db_initialize()
        return conn_check

        # 初始化数据库：如果内容为空，则创建表初始化

    def db_initialize(self):
        print("——初始化数据库：如果内容为空，则创建表初始化")
        conn = sqlite3.connect(self.db_filepath)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_text'")

        if c.fetchone() is None:
            print("db is empty, write new table.")
            self.db_create_table()
            now = datetime.datetime.now()
            now_name = now.strftime("%Y-%m-%d_%H-%M-%S")
            now_time = int(date_to_seconds(now_name))
            self.db_update_data(
                now_name + ".mp4",
                '0.jpg',
                now_time,
                'Welcome! Go to Setting and Update your screen recording files.',
                False,
                False,
                'base64'
            )
        else:
            print("db existed and not empty")

    # 重新读取配置文件
    def db_update_read_config(self, config):
        self.db_max_page_result = int(config["max_page_result"])

    # 初始化数据库：检查、创建、连接数据库对象
    def db_check_exist(self):
        print("——初始化数据库：检查、创建、连接数据库对象")
        is_db_exist = False
        # 检查数据库是否存在
        if not os.path.exists(self.db_filepath):
            print("db not existed")
            is_db_exist = False
            if not os.path.exists(self.db_filepath):
                os.mkdir(self.db_filepath)
                print("db dir not existed, mkdir")
        else:
            is_db_exist = True

        # 连接/创建数据库
        conn = sqlite3.connect(self.db_filepath)
        conn.close()
        return is_db_exist

    # 创建表
    def db_create_table(self):
        print("——创建表")
        conn = sqlite3.connect(self.db_filepath)
        conn.execute('''CREATE TABLE video_text  
                   (videofile_name VARCHAR(100),
                   picturefile_name VARCHAR(100),
                   videofile_time INT, 
                   ocr_text TEXT,
                   is_videofile_exist BOOLEAN,
                   is_picturefile_exist BOOLEAN,
                   thumbnail TEXT);''')
        conn.close()

    # 插入数据
    def db_update_data(self, videofile_name, picturefile_name, videofile_time, ocr_text, is_videofile_exist,
                       is_picturefile_exist, thumbnail):
        print("——插入数据")
        # 使用方法：db_update_data(db_filepath,'video1.mp4','iframe_0.jpg', 120, 'text from ocr', True, False)
        conn = sqlite3.connect(self.db_filepath)
        c = conn.cursor()

        c.execute(
            "INSERT INTO video_text (videofile_name, picturefile_name, videofile_time, ocr_text, is_videofile_exist, is_picturefile_exist, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (videofile_name, picturefile_name, videofile_time, ocr_text, is_videofile_exist, is_picturefile_exist,
             thumbnail))
        conn.commit()
        conn.close()

    # 查询关键词数据
    def db_search_data(self, keyword_input, date_in, date_out, page_index):
        print("——查询关键词数据")
        with open('config.json', encoding='utf-8') as f:
            config = json.load(f)
        self.db_update_read_config(config)
        date_in_ts = int(date_to_seconds(date_in.strftime("%Y-%m-%d_00-00-00")))
        date_out_ts = int(date_to_seconds(date_out.strftime("%Y-%m-%d_23-59-59")))
        start_from = 0 + page_index * self.db_max_page_result
        end_from = self.db_max_page_result + page_index * self.db_max_page_result
        limit = end_from - start_from + 1
        offset = start_from - 1

        conn = sqlite3.connect(self.db_filepath)
        df = pd.read_sql_query(f"""
                              SELECT * FROM video_text 
                              WHERE ocr_text LIKE '%{keyword_input}%' 
                              AND videofile_time BETWEEN {date_in_ts} AND {date_out_ts} 
                              LIMIT {limit} OFFSET {offset}"""
                               , conn)
        conn.close()
        return df

    # 优化搜索数据结果的展示
    def db_refine_search_data(self, df):
        print("——优化搜索数据结果的展示")
        df.drop('picturefile_name', axis=1, inplace=True)
        df.drop('is_picturefile_exist', axis=1, inplace=True)

        df.insert(1, 'time_stamp', df['videofile_time'].apply(seconds_to_date))
        # df.drop('videofile_time', axis=1, inplace=True)

        df.insert(len(df.columns) - 1, 'videofile_name', df.pop('videofile_name'))
        df.insert(len(df.columns) - 1, 'videofile_time', df.pop('videofile_time'))
        # df['is_videofile_exist'] = df['is_videofile_exist'].astype(str)

        df['thumbnail'] = 'data:image/png;base64,' + df['thumbnail']
        df.insert(0, 'thumbnail', df.pop('thumbnail'))

        return df

    # 列出所有数据
    def db_print_all_data(self):
        print("——列出所有数据")
        # 获取游标
        # 使用SELECT * 从video_text表查询所有列的数据
        # 使用fetchall()获取所有结果行
        # 遍历结果行,打印出每一行
        conn = sqlite3.connect(self.db_filepath)
        c = conn.cursor()
        c.execute("SELECT * FROM video_text")
        rows = c.fetchall()
        for row in rows:
            print(row)
        conn.close()

    # 查询数据库一共有多少行
    def db_num_records(self):
        print("——查询数据库一共有多少行")
        conn = sqlite3.connect(self.db_filepath)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM video_text")
        rows_count = c.fetchone()[0]
        conn.close()
        print(f"rows_count: {rows_count}")
        return rows_count

    # 获取表内最新的记录时间
    def db_latest_record_time(self):
        conn = sqlite3.connect(self.db_filepath)
        c = conn.cursor()

        c.execute("SELECT MAX(videofile_time) FROM video_text")
        max_time = c.fetchone()[0]
        conn.close()
        return max_time


with open('config.json', encoding='utf-8') as f:
    config = json.load(f)
dbManager = DBManager(
    config["db_path"],
    config["db_filename"],
    os.path.join(config["db_path"], config["db_filename"]),
    int(config["max_page_result"])
)
