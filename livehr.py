# import streamlit as st

# # MUST BE FIRST STREAMLIT COMMAND
# st.set_page_config(
#     page_title="Live Heart Rate Dashboard",
#     layout="wide"
# )

# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build

# import datetime
# import pandas as pd
# import pickle
# import os
# import time

# # ----------------------------
# # GOOGLE FIT SCOPES
# # ----------------------------
# SCOPES = [
#     'https://www.googleapis.com/auth/fitness.activity.read',
#     'https://www.googleapis.com/auth/fitness.heart_rate.read'
# ]

# # ----------------------------
# # LOGIN FUNCTION
# # ----------------------------
# @st.cache_resource
# def get_service():

#     creds = None

#     # Load token if exists
#     if os.path.exists("token.pkl"):

#         with open("token.pkl", "rb") as token:
#             creds = pickle.load(token)

#     # Login if needed
#     if not creds or not creds.valid:

#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())

#         else:

#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json',
#                 SCOPES
#             )

#             creds = flow.run_local_server(port=0)

#         # Save token
#         with open("token.pkl", "wb") as token:
#             pickle.dump(creds, token)

#     service = build(
#         'fitness',
#         'v1',
#         credentials=creds
#     )

#     return service


# service = get_service()

# # ----------------------------
# # PAGE TITLE
# # ----------------------------
# st.title("❤️ Live Heart Rate Dashboard")

# placeholder = st.empty()

# # ----------------------------
# # HR RATING FUNCTION
# # ----------------------------
# def get_rating(hr):

#     if hr < 60:
#         return "Low"

#     elif hr <= 100:
#         return "Normal"

#     elif hr <= 120:
#         return "High"

#     else:
#         return "Very High"


# # ----------------------------
# # INDIA TIMEZONE
# # ----------------------------
# india_timezone = datetime.timezone(
#     datetime.timedelta(hours=5, minutes=30)
# )

# # ----------------------------
# # LIVE LOOP
# # ----------------------------
# while True:

#     try:

#         # Current IST time
#         end_time = datetime.datetime.now(
#             datetime.timezone.utc
#         )

#         # Last 24 hours
#         start_time = end_time - datetime.timedelta(hours=24)

#         # Google Fit aggregate request
#         body = {
#             "aggregateBy": [{
#                 "dataTypeName": "com.google.heart_rate.bpm"
#             }],
#             "bucketByTime": {
#                 "durationMillis": 60000
#             },
#             "startTimeMillis": int(start_time.timestamp() * 1000),
#             "endTimeMillis": int(end_time.timestamp() * 1000)
#         }

#         result = service.users().dataset().aggregate(
#             userId="me",
#             body=body
#         ).execute()

#         records = []

#         for bucket in result.get("bucket", []):

#             for dataset in bucket.get("dataset", []):

#                 for point in dataset.get("point", []):

#                     values = point.get("value", [])

#                     if values:

#                         hr = values[0].get("fpVal")

#                         if hr:

#                             # UTC timestamp
#                             start_ns = int(
#                                 point["startTimeNanos"]
#                             )

#                             utc_time = datetime.datetime.fromtimestamp(
#                                 start_ns / 1e9,
#                                 tz=datetime.timezone.utc
#                             )

#                             # Convert to IST
#                             local_time = utc_time.astimezone(
#                                 india_timezone
#                             )

#                             records.append({
#                                 "Time": local_time.strftime(
#                                     "%H:%M"
#                                 ),
#                                 "Heart Rate": round(hr),
#                                 "Rating": get_rating(hr)
#                             })

#         with placeholder.container():

#             if len(records) > 0:

#                 latest = records[-1]

#                 # METRICS
#                 col1, col2, col3 = st.columns(3)

#                 col1.metric(
#                     "Current HR",
#                     f"{latest['Heart Rate']} BPM"
#                 )

#                 col2.metric(
#                     "Rating",
#                     latest["Rating"]
#                 )

#                 col3.metric(
#                     "Last Update",
#                     latest["Time"]
#                 )

#                 # TABLE
#                 df = pd.DataFrame(records)

#                 # Latest first
#                 df = df[::-1]

#                 st.dataframe(
#                     df,
#                     use_container_width=True,
#                     hide_index=True
#                 )

#             else:

#                 st.warning(
#                     "No heart rate data found"
#                 )

#     except Exception as e:

#         st.error(str(e))

#     # Refresh every 30 sec
#     time.sleep(30)

#     st.rerun()
import streamlit as st

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Live Heart Rate Dashboard",
    layout="wide"
)

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import datetime
import pandas as pd
import pickle
import os
import time

# -----------------------------------
# GOOGLE FIT SCOPES
# -----------------------------------
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.oxygen_saturation.read'
]

# -----------------------------------
# GOOGLE FIT LOGIN
# -----------------------------------
@st.cache_resource
def get_service():

    creds = None

    # Load saved token
    if os.path.exists("token.pkl"):

        with open("token.pkl", "rb") as token:
            creds = pickle.load(token)

    # Login if needed
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        # Save token
        with open("token.pkl", "wb") as token:
            pickle.dump(creds, token)

    service = build(
        'fitness',
        'v1',
        credentials=creds
    )

    return service


service = get_service()

# -----------------------------------
# PAGE TITLE
# -----------------------------------
st.title("❤️ Live Heart Rate Dashboard")

placeholder = st.empty()

# -----------------------------------
# HEART RATE RATING
# -----------------------------------
def get_rating(hr):

    if hr < 60:
        return "Low"

    elif hr <= 100:
        return "Normal"

    elif hr <= 120:
        return "High"

    else:
        return "Very High"

# -----------------------------------
# INDIA TIMEZONE
# -----------------------------------
india_timezone = datetime.timezone(
    datetime.timedelta(hours=5, minutes=30)
)

# -----------------------------------
# LIVE LOOP
# -----------------------------------
while True:

    try:

        # Current UTC time
        end_time = datetime.datetime.now(
            datetime.timezone.utc
        )

        # Last 24 hours
        start_time = end_time - datetime.timedelta(
            hours=24
        )

        # Google Fit aggregate request for Heart Rate
        body_hr = {
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_rate.bpm"
            }],
            "bucketByTime": {
                "durationMillis": 60000
            },
            "startTimeMillis": int(
                start_time.timestamp() * 1000
            ),
            "endTimeMillis": int(
                end_time.timestamp() * 1000
            )
        }

        # Google Fit aggregate request for Oxygen Saturation
        body_spo2 = {
            "aggregateBy": [{
                "dataTypeName": "com.google.oxygen_saturation"
            }],
            "bucketByTime": {
                "durationMillis": 60000
            },
            "startTimeMillis": int(
                start_time.timestamp() * 1000
            ),
            "endTimeMillis": int(
                end_time.timestamp() * 1000
            )
        }

        result_hr = service.users().dataset().aggregate(
            userId="me",
            body=body_hr
        ).execute()

        result_spo2 = service.users().dataset().aggregate(
            userId="me",
            body=body_spo2
        ).execute()

        data_by_time = {}

        # -----------------------------------
        # PARSE HEART RATE DATA
        # -----------------------------------
        for bucket in result_hr.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    values = point.get("value", [])
                    if values:
                        hr = values[0].get("fpVal")
                        if hr:
                            start_ns = int(point["startTimeNanos"])
                            utc_time = datetime.datetime.fromtimestamp(
                                start_ns / 1e9, tz=datetime.timezone.utc
                            )
                            local_time = utc_time.astimezone(india_timezone)
                            
                            if local_time not in data_by_time:
                                data_by_time[local_time] = {
                                    "Datetime": local_time,
                                    "Time": local_time.strftime("%H:%M"),
                                    "Heart Rate": None,
                                    "Rating": None,
                                    "SpO2 (%)": None
                                }
                            
                            data_by_time[local_time]["Heart Rate"] = round(hr)
                            data_by_time[local_time]["Rating"] = get_rating(hr)

        # -----------------------------------
        # PARSE OXYGEN SATURATION DATA
        # -----------------------------------
        for bucket in result_spo2.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    values = point.get("value", [])
                    if values:
                        spo2 = values[0].get("fpVal")
                        if spo2:
                            start_ns = int(point["startTimeNanos"])
                            utc_time = datetime.datetime.fromtimestamp(
                                start_ns / 1e9, tz=datetime.timezone.utc
                            )
                            local_time = utc_time.astimezone(india_timezone)
                            
                            if local_time not in data_by_time:
                                data_by_time[local_time] = {
                                    "Datetime": local_time,
                                    "Time": local_time.strftime("%H:%M"),
                                    "Heart Rate": None,
                                    "Rating": None,
                                    "SpO2 (%)": None
                                }
                            
                            data_by_time[local_time]["SpO2 (%)"] = round(spo2, 1)

        records = list(data_by_time.values())

        with placeholder.container():

            if len(records) > 0:

                # -----------------------------------
                # SORT LATEST FIRST
                # -----------------------------------
                records = sorted(
                    records,
                    key=lambda x: x["Datetime"],
                    reverse=True
                )

                latest = records[0]

                # -----------------------------------
                # METRICS
                # -----------------------------------
                col1, col2, col3, col4 = st.columns(4)

                hr_val = latest["Heart Rate"]
                hr_disp = f"{hr_val} BPM" if pd.notna(hr_val) and hr_val else "N/A"
                col1.metric("Current HR", hr_disp)

                rating_disp = latest["Rating"] if pd.notna(latest["Rating"]) and latest["Rating"] else "N/A"
                col2.metric("Rating", rating_disp)

                spo2_val = latest["SpO2 (%)"]
                spo2_disp = f"{spo2_val}%" if pd.notna(spo2_val) and spo2_val else "N/A"
                col3.metric("SpO2", spo2_disp)

                col4.metric("Last Update", latest["Time"])

                # -----------------------------------
                # TABLE
                # -----------------------------------
                df = pd.DataFrame(records)

                # REMOVE DUPLICATES
                df = df.drop_duplicates()

                # SORT BY TIME
                df = df.sort_values(
                    by="Datetime",
                    ascending=False
                )
                
                df = df.drop(columns=["Datetime"])

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.warning(
                    "No heart rate data found"
                )

    except Exception as e:

        st.error(str(e))

    # -----------------------------------
    # AUTO REFRESH
    # -----------------------------------
    time.sleep(30)

    st.rerun()