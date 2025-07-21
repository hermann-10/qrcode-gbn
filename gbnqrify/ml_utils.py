import pandas as pd
from sklearn.cluster import KMeans
from django.utils import timezone
from gbnqrify.models import Attendance

def preprocess_attendance():
    records = Attendance.objects.all().values('employee_id', 'session', 'time', 'date')
    df = pd.DataFrame.from_records(records)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    df['minutes'] = df['time'].apply(lambda x: x.hour * 60 + x.minute)
    df_am = df[df['session'] == 'AM']
    df_pm = df[df['session'] == 'PM']
    return df_am, df_pm

def cluster_attendance(df, n_clusters=3):
    if df.empty or len(df) < n_clusters:
        return df, None
    X = df[['minutes']]
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df = df.copy()
    df['cluster'] = kmeans.fit_predict(X)
    df['cluster_center'] = df['cluster'].apply(lambda x: kmeans.cluster_centers_[x][0])
    return df, kmeans

def predict_cluster(session, minutes):
    df_am, df_pm = preprocess_attendance()
    df, model = cluster_attendance(df_am if session == 'AM' else df_pm)
    if model is None:
        return None
    cluster_label = model.predict([[minutes]])[0]
    return cluster_label

def interpret_cluster(session, label):
    mapping = {
        0: "You're among the early arrivals.",
        1: "You arrived on time.",
        2: "You're late today."
    }
    return mapping.get(label, "Attendance recorded.")