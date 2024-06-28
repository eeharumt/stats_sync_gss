import pandas as pd
from sqlalchemy import create_engine
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import time

user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
host = os.environ.get("DB_HOST")
db_name = os.environ.get("DB_NAME")

# Google Spreadsheetの認証情報
def authenticate_google_docs():
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('./credentials/google_credentials.json', scope)
    client = gspread.authorize(creds)
    return client

# データベースから1日分のデータを読み込む
def fetch_data():
    DATABASE_URL = "mysql+pymysql://{user}:{password}@{host}/{db_name}"
    print(DATABASE_URL)
    engine = create_engine(DATABASE_URL)

    # MySQLデータベース接続設定
    query = """
    SELECT recorded_at, job_name, count_on_duty, count_off_duty
    FROM mistate_job_stats
    WHERE DATE(recorded_at) = CURDATE()
    ORDER BY recorded_at, job_name;
    """

    df = pd.read_sql(query, engine)
    return df

def format_data(df):
    # 新しいDataFrameを作成（各ジョブと時間でのonduty/offdutyを表示）
    formatted_df = pd.DataFrame(index=pd.to_datetime(df['recorded_at']).dt.round('15min').unique())
    
    # DataFrameのインデックスを文字列形式に変換
    formatted_df.index = formatted_df.index.strftime('%Y-%m-%d %H:%M:%S')

    # 各ジョブごとに列を追加
    for (recorded_at, job_name), group in df.groupby(['recorded_at', 'job_name']):
        timestamp = pd.to_datetime(recorded_at).strftime('%Y-%m-%d %H:%M:%S')
        formatted_df.loc[timestamp, f'{job_name} onduty'] = group['count_on_duty'].values[0]
        formatted_df.loc[timestamp, f'{job_name} offduty'] = group['count_off_duty'].values[0]

    # NaNを0に変換
    formatted_df = formatted_df.fillna(0).astype(int)
    return formatted_df

# Google Spreadsheetにデータを書き込む
def upload_to_spreadsheet(df, client):
    # 1Ic2JirkIdKtYq9Ligl_nMVlw4e6XNLw7VDaE8savOzU は共有スプレッドシート
    # 
    spreadsheet = client.open_by_key('1Ic2JirkIdKtYq9Ligl_nMVlw4e6XNLw7VDaE8savOzU').worksheet('Sheet1')
    
    # 毎回列名は追加（仕事の増減あると思うので…）
    spreadsheet.append_row(['timestamp'] + df.columns.values.tolist())
    
    # DataFrameを行ごとにアップロード
    for index, row in df.iterrows():
        spreadsheet.append_row([index] + row.tolist())  

def main():
    client = authenticate_google_docs()
    df = fetch_data()
    df = format_data(df)
    upload_to_spreadsheet(df, client)

if __name__ == '__main__':
    main()
