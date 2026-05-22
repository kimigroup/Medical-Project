import pandas as pd
import re
import pyodbc
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://@./Bronze_DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
engine_clean = create_engine(
    "mssql+pyodbc://@./Silver_DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

# detrmine data frame names
all_data ={'analysis_df':'analysis',
           'test_df':'test',
           'normal_df':'normal',
           
           'patient_df':'Patients_data',
           
           }
df={}

# read data set from csv set it in data frame in dictionary 
# then see inf for every data frame and test if null value in it 
for df_name,dat in all_data.items():
    df[df_name] = pd.read_excel(f"{dat}.xlsx")
    print(f"the file name {dat}")
    # create Bronze in SQL DWH

    df[df_name].to_sql(
    name=f"{dat}",       
    con=engine,
    if_exists="replace",      
    index=False              
    )
    
    print(df[df_name].info())
    print(df[df_name].isnull().sum())
    print(df[df_name])
    print("-" * 100)

#read data from Access
path = "G:/رواد مصر الرقمية 4/PROJECT/Py/Lab.mdb"
conn = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + path)
result_df = pd.read_sql("SELECT * FROM [result]", conn)
conn.close()
result_df.to_sql(
    name="result",       
    con=engine,
    if_exists="replace",      
    index=False              
    )
print(result_df.info())
print(result_df.isnull().sum())
print(result_df)
print("-" * 100)

# change null value in test data frame column unit chnge null with (--)
df['test_df']['unit'] = df['test_df']['unit'].fillna('No Unit')

print(df['test_df'].info())

Patients_data_df = df['patient_df'] 

# count value 
counts = Patients_data_df['gender'].value_counts()
print("Counts of Gender:")
print(counts)

counts = Patients_data_df['City'].value_counts()
print("Counts of city:")
print(counts)

# توحيد قيم النوع
Patients_data_df.replace('انثى', 'F', regex=True, inplace=True)
Patients_data_df.replace('أنثى', 'F', regex=True, inplace=True)
Patients_data_df.replace('ذكر', 'M', regex=True, inplace=True)

counts = Patients_data_df['gender'].value_counts()
print("Counts of Gender:")
print(counts)

# توحيد طريقه حساب السن
mixed_age_rows = Patients_data_df[Patients_data_df['Age'].astype(str).str.contains(r'[a-zA-Z\u0600-\u06FF]', na=False)]
print(mixed_age_rows[['Age']])


def clean_medical_age(age_value):
    # تحويل لـ string وتصغير الحروف وتجهيز النص
    text = str(age_value).lower().strip()
    
    # 1. معالجة الكلمات الخاصة اللي مفيش فيها أرقام واضحة
    if text == 'سنه' or text == 'سنة':
        return 1.0
    if text == 'شهرين':
        return round(2 / 12, 2)
    if text == 'شهر':
        return round(1 / 12, 2)

    # 2. استخراج الرقم من النص (لو موجود)
    numbers = re.findall(r"\d+", text)
    num = float(numbers[0]) if numbers else None
    
    if num is None:
        return None

    # 3. تحديد وحدة القياس والتحويل لسنين
    # التحويل لأيام
    if any(word in text for word in ['يوم', 'أيام', 'day', 'days']):
        return round(num / 365, 3)
    
    # التحويل لشهور
    elif any(word in text for word in ['شهر', 'شهور', 'month']):
        return round(num / 12, 2)
    
    # التحويل لسنين (Default)
    elif any(word in text for word in ['سنة', 'سنوات', 'year']):
        return num
    
    # لو رقم فقط بدون تمييز، هنفترض إنه سنين
    else:
        return num


Patients_data_df['Age_Clean'] = Patients_data_df['Age'].apply(clean_medical_age)

mixed_cases = df['patient_df'][df['patient_df']['Age'].astype(str).str.contains(r'[آ-يa-zA-Z]', na=False)]
print(mixed_cases[['Age', 'Age_Clean']])
print(Patients_data_df['Age_Clean'])
print(Patients_data_df['Age_Clean'].describe())

print(Patients_data_df.info())


# القيم الغير موجوده فى جدول normal
print(df['normal_df'][df['normal_df']['normal'].isnull()])

df['normal_df'] = pd.merge(df['test_df'], df['normal_df'], left_on='id_t', right_on='id_t')
print(df['normal_df'][df['normal_df']['normal'].isnull()])

# مسح التكرار
df['analysis_df'].drop_duplicates(subset=['name_an'],keep='first',inplace=True)
print(df['analysis_df'].info())

df['test_df'].drop_duplicates(subset=['name_t'],keep='first',inplace=True)
print(df['test_df'].info())

df['normal_df'].drop_duplicates(subset=['id_t'],keep='first',inplace=True)
print(df['normal_df'].info())



Patients_data_df.drop_duplicates(subset=['id_m'],keep='first',inplace=True)
print(Patients_data_df.info())

# create Silver in SQL DWH
result_df.to_sql(
    name="result",       
    con=engine_clean,
    if_exists="replace",      
    index=False              
    )
for df_name,dat in all_data.items():
    df[df_name].to_sql(
    name=f"{dat}",       
    con=engine_clean,
    if_exists="replace",      
    index=False              
    )

