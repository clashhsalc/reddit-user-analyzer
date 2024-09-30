import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def get_user_data(username):
    all_comments = []
    after = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }

    while True:
        url = f"https://www.reddit.com/user/{username}/comments.json?limit=99"
        if after:
            url += f"&after={after}"

        response = requests.get(url, headers=headers)

        #returns an error when hosted on streamlit community cloud (unfixed)
        if response.status_code == 403:
            st.error("Access forbidden: Reddit is blocking the request. Try a different network or method.")
            return None
        elif response.status_code != 200:
            st.error(f"Error fetching data: {response.status_code}")
            return None

        data = response.json()

        if 'data' not in data or 'children' not in data['data']:
            return None

        comments = [item['data'] for item in data['data']['children'] if item['kind'] == 't1']
        all_comments.extend(comments)

        after = data['data']['after']
        if not after:
            break

    return all_comments

def analyze_user_data(comments):
    if not comments:
        return None

    df = pd.DataFrame(comments)

    total_comments = len(comments)
    total_karma = df['score'].sum()
    avg_karma = total_karma / total_comments if total_comments > 0 else 0

    subreddits = df['subreddit'].value_counts().head(10) if 'subreddit' in df else "No data found"
    karma_by_subreddit = df.groupby('subreddit')['score'].sum().sort_values(ascending=False).head(10) if 'subreddit' in df else "No data found"

    if 'created_utc' in df:
        time_data = pd.to_datetime(df['created_utc'], unit='s')
        activity_by_hour = time_data.dt.hour.value_counts().sort_index()
        activity_by_day = time_data.dt.day_name().value_counts()
        first_comment_date = time_data.min()
        last_comment_date = time_data.max()
        days_active = (last_comment_date - first_comment_date).days
        comments_per_day = total_comments / days_active if days_active > 0 else 0
    else:
        activity_by_hour, activity_by_day, first_comment_date, last_comment_date, comments_per_day = ["No data found"] * 5

    most_upvoted_comment = df.loc[df['score'].idxmax()] if not df.empty else "No data found"
    most_downvoted_comment = df.loc[df['score'].idxmin()] if not df.empty else "No data found"
    avg_comment_length = df['body'].str.len().mean() if 'body' in df else "No data found"

    return {
        'total_comments': total_comments,
        'total_karma': total_karma,
        'avg_karma': avg_karma,
        'subreddits': subreddits,
        'karma_by_subreddit': karma_by_subreddit,
        'activity_by_hour': activity_by_hour,
        'activity_by_day': activity_by_day,
        'most_upvoted_comment': most_upvoted_comment,
        'most_downvoted_comment': most_downvoted_comment,
        'avg_comment_length': avg_comment_length,
        'first_comment_date': first_comment_date,
        'last_comment_date': last_comment_date,
        'comments_per_day': comments_per_day,
        'all_comments': df
    }

def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(plt)

def main():
    st.title("Reddit User Analyzer")

    username = st.text_input("Enter Reddit username:")

    if username:
        with st.spinner("Fetching and analyzing data..."):
            user_data = get_user_data(username)

            if user_data is None:
                st.error("No data found for this user or the user does not exist.")
                return

            analysis = analyze_user_data(user_data)

            if analysis is None:
                st.error("No comments found for this user.")
                return

            st.header(f"Analysis for u/{username}")

            tab1, tab2 = st.tabs(["Overview", "Comments and Posts"])

            with tab1:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Comments", analysis['total_comments'])
                col2.metric("Total Karma", analysis['total_karma'])
                col3.metric("Average Karma per Comment", f"{analysis['avg_karma']:.2f}")

                st.subheader("Top Subreddits")
                if isinstance(analysis['subreddits'], pd.Series):
                    fig_subreddits = px.bar(analysis['subreddits'], title="Top 10 Subreddits by Comment Count")
                    st.plotly_chart(fig_subreddits)
                else:
                    st.write("No data found for subreddits.")

                st.subheader("Karma by Subreddit")
                if isinstance(analysis['karma_by_subreddit'], pd.Series):
                    fig_karma = px.bar(analysis['karma_by_subreddit'], title="Top 10 Subreddits by Karma")
                    st.plotly_chart(fig_karma)
                else:
                    st.write("No data found for karma by subreddit.")

                st.subheader("Activity by Hour")
                if isinstance(analysis['activity_by_hour'], pd.Series):
                    fig_hour = px.bar(analysis['activity_by_hour'], title="Activity by Hour of Day")
                    st.plotly_chart(fig_hour)
                else:
                    st.write("No data found for activity by hour.")

                st.subheader("Activity by Day")
                if isinstance(analysis['activity_by_day'], pd.Series):
                    fig_day = px.bar(analysis['activity_by_day'], title="Activity by Day of Week")
                    st.plotly_chart(fig_day)
                else:
                    st.write("No data found for activity by day.")

                st.subheader("Additional Insights")
                st.write(f"Average comment length: {analysis['avg_comment_length']}")
                st.write(f"First comment date: {analysis['first_comment_date']}")
                st.write(f"Last comment date: {analysis['last_comment_date']}")
                st.write(f"Comments per day: {analysis['comments_per_day']}")

                st.subheader("Most Upvoted Comment")
                if isinstance(analysis['most_upvoted_comment'], pd.Series):
                    st.write(f"Subreddit: r/{analysis['most_upvoted_comment']['subreddit']}")
                    st.write(f"Score: {analysis['most_upvoted_comment']['score']}")
                    st.write(f"Comment: {analysis['most_upvoted_comment']['body']}")
                    permalink = f"https://www.reddit.com{analysis['most_upvoted_comment']['permalink']}"
                    st.write(f"[Permalink]({permalink})")
                else:
                    st.write("No data found for most upvoted comment.")

                st.subheader("Most Downvoted Comment")
                if isinstance(analysis['most_downvoted_comment'], pd.Series):
                    st.write(f"Subreddit: r/{analysis['most_downvoted_comment']['subreddit']}")
                    st.write(f"Score: {analysis['most_downvoted_comment']['score']}")
                    st.write(f"Comment: {analysis['most_downvoted_comment']['body']}")
                    permalink = f"https://www.reddit.com{analysis['most_downvoted_comment']['permalink']}"
                    st.write(f"[Permalink]({permalink})")
                else:
                    st.write("No data found for most downvoted comment.")

                st.subheader("Word Cloud of Comments")
                if 'body' in pd.DataFrame(user_data):
                    all_text = ' '.join(comment['body'] for comment in user_data)
                    generate_wordcloud(all_text)
                else:
                    st.write("No comment text found for word cloud.")

            with tab2:
                st.subheader("All Comments and Posts")
                if analysis['all_comments'].empty:
                    st.write("No comments found.")
                else:
                    for index, row in analysis['all_comments'].iterrows():
                        st.write(f"**Subreddit:** r/{row['subreddit']}")
                        st.write(f"**Score:** {row['score']}")
                        st.write(f"**Comment:** {row['body']}")
                        permalink = f"https://www.reddit.com{row['permalink']}"
                        st.write(f"[Permalink]({permalink})")
                        st.write("---")

if __name__ == "__main__":
    main()
