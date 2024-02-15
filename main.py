# Import libraries
import streamlit as st
import pandas as pd
from passlib.hash import bcrypt
from datetime import datetime
import os
import sqlite3
import time

# Set page config
st.set_page_config(
    page_title="Glyde",
    page_icon=":purple_heart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Create SQLite database and tables
conn = sqlite3.connect('social_media.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        video TEXT,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        comments TEXT,
        timestamp DATETIME NOT NULL,
        visibility TEXT NOT NULL
    )
''')

conn.commit()

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = bcrypt.hash(password)

# Initialize a list to store user instances
registered_users = []

# Time delay for login attempts (in seconds)
LOGIN_DELAY = 5

# Part 1: Maintain User Session on Refresh
# Set user to None only if it is not present in the session state
if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.upvoted_posts = {}
    st.session_state.downvoted_posts = {}
    st.session_state.login_attempt_time = 0
    st.session_state.page_number = 1  # Initialize the page_number with a key


def get_user():
    return st.session_state.user

def is_duplicate_user(username, email):
    cursor.execute('''
        SELECT * FROM users WHERE username = ? OR email = ?
    ''', (username, email))
    existing_user = cursor.fetchone()
    return existing_user is not None

def register_user(username, email, password):
    if not is_duplicate_user(username, email):
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, bcrypt.hash(password)))
        conn.commit()
        return True
    else:
        return False

def login_user(email, password):
    cursor.execute('''
        SELECT * FROM users WHERE email = ?
    ''', (email,))
    user_data = cursor.fetchone()
    if user_data and bcrypt.verify(password, user_data[3]):
        return User(user_data[1], user_data[2], password)
    return None

def add_post(username, title, content, video, visibility):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO posts (username, title, content, video, visibility, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, title, content, video, visibility, timestamp))
    conn.commit()

def add_comment(post_id, comment):
    cursor.execute('''
        SELECT comments FROM posts WHERE id = ?
    ''', (post_id,))
    comments_data = cursor.fetchone()
    comments = eval(comments_data[0]) if comments_data and comments_data[0] else []
    comments.append(comment)
    cursor.execute('''
        UPDATE posts SET comments = ? WHERE id = ?
    ''', (str(comments), post_id))
    conn.commit()

def upvote_post(post_id, user_id):
    cursor.execute('''
        SELECT upvotes, downvotes FROM posts WHERE id = ?
    ''', (post_id,))
    votes_data = cursor.fetchone()
    upvotes, downvotes = votes_data if votes_data else (0, 0)

    if user_id not in eval(st.session_state.get('upvoted_posts', {}).get(str(post_id), '[]')):
        upvotes += 1
        st.session_state.upvoted_posts[str(post_id)] = str(eval(st.session_state.get('upvoted_posts', {}).get(str(post_id), '[]')) + [user_id])
        cursor.execute('''
            UPDATE posts SET upvotes = ? WHERE id = ?
        ''', (upvotes, post_id))
        conn.commit()

def downvote_post(post_id, user_id):
    cursor.execute('''
        SELECT upvotes, downvotes FROM posts WHERE id = ?
    ''', (post_id,))
    votes_data = cursor.fetchone()
    upvotes, downvotes = votes_data if votes_data else (0, 0)

    if user_id not in eval(st.session_state.get('downvoted_posts', {}).get(str(post_id), '[]')):
        downvotes += 1
        st.session_state.downvoted_posts[str(post_id)] = str(eval(st.session_state.get('downvoted_posts', {}).get(str(post_id), '[]')) + [user_id])
        cursor.execute('''
            UPDATE posts SET downvotes = ? WHERE id = ?
        ''', (downvotes, post_id))
        conn.commit()

# Part 2: Implement Bot/Spam/DDoS Protection (Captcha Check Removed)

# Part 2: Implement Bot/Spam/DDoS Protection (Captcha Check Removed)

# Part 3: Pagination
# Main function
def main():
    # Define the 'page' variable at the beginning of the function
    pages = ["Home", "Login", "Sign Up", "Create Post"]
    page = st.sidebar.radio("Go to", pages)

    st.title("Glyde Social Media App")
    st.sidebar.header("Navigation")

    if st.session_state.user is not None:
        st.sidebar.write(f"Logged in as {st.session_state.user.username}")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
    else:
        st.sidebar.write("Not logged in")

    # Use the session state directly
    user = st.session_state.user

    # ...

    if page == "Home":
        st.header("Welcome to the Home Page")

        # Pagination
        posts_per_page = 5  # You can adjust the number of posts per page
        page_number = st.session_state.page_number  # Use the session_state key

        # Calculate the offset based on the page number
        offset = (page_number - 1) * posts_per_page

        # Display posts based on visibility and search term with pagination
        query = f'''
            SELECT * FROM posts 
            WHERE visibility = 'Public' 
            ORDER BY timestamp DESC
            LIMIT {posts_per_page} OFFSET {offset}
        '''
        cursor.execute(query)
        posts_data = cursor.fetchall()

        # Display posts and implement next and previous page logic
        for post in posts_data:
            with st.container():
                st.markdown(f"<h3 style='color:purple;'>{post[2]}</h3> by {post[1]} on {post[8]}", unsafe_allow_html=True)
                st.markdown(f"<p style='color:purple;'>{post[3]}</p>", unsafe_allow_html=True)
                if post[4]:
                    st.video(post[4])
                st.markdown(f"<p style='color:purple;'>Upvotes: {post[5]} | Downvotes: {post[6]}</p>", unsafe_allow_html=True)

                # Upvote and Downvote buttons
                upvote_button = st.button(f"Upvote ({post[5]})", key=f"upvote_{post[0]}")
                downvote_button = st.button(f"Downvote ({post[6]})", key=f"downvote_{post[0]}")

                if user is not None:
                    user_id = user.username

                    if upvote_button:
                        upvote_post(post[0], user_id)
                    if downvote_button:
                        downvote_post(post[0], user_id)

                # Display comments
                st.subheader("Comments")
                comments = eval(post[7]) if post[7] else []
                for comment in comments:
                    comment_parts = comment.split(": ", 1)
                    if len(comment_parts) == 2:
                        username, comment_text = comment_parts
                        st.write(f"<p style='color:purple;'>{username}: {comment_text}</p>", unsafe_allow_html=True)
                    else:
                        st.write(f"<p style='color:purple;'>{comment}</p>", unsafe_allow_html=True)

                # Add a comment
                new_comment = st.text_area(f"Add a comment to {post[2]}")
                if st.button(f"Post Comment to {post[0]}", key=f"comment_{post[0]}"):
                    add_comment(post[0], f"{user.username}: {new_comment}")

                st.markdown("---")

        # Next and previous page buttons
        if st.button("Next Page", key="next_page"):
            st.session_state.page_number += 1
        if st.button("Previous Page", key="prev_page"):
            st.session_state.page_number = max(1, page_number - 1)

    # ...

# Rest of the code remains the same


    elif page == "Login":
        st.header("Login")

        if st.session_state.login_attempt_time > time.time() - LOGIN_DELAY:
            st.warning(f"Please wait for {LOGIN_DELAY} seconds before attempting to login again.")
        else:
            email = st.text_input("Email:")
            password = st.text_input("Password:", type="password")
            login_button = st.button("Login")

            if login_button:
                user = login_user(email, password)
                if user is not None:
                    st.session_state.user = user
                    st.session_state.login_attempt_time = 0
                    st.success("Login successful!")
                    st.balloons()
                else:
                    st.session_state.login_attempt_time = time.time()
                    st.error("Invalid email or password.")

    elif page == "Sign Up":
        st.header("Sign Up")

        username = st.text_input("Username:")
        email = st.text_input("Email:")
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")
        register_button = st.button("Register")

        if register_button:
            if password == confirm_password:
                if register_user(username, email, password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username or email already exists.")
            else:
                st.error("Passwords do not match.")

    elif page == "Create Post":
        st.header("Create a Post")

        title = st.text_input("Title:")
        content = st.text_area("Content:")
        video = st.file_uploader("Upload Video (Optional)", type=["mp4", "avi", "mov"])
        visibility = "Public"  # Always public now

        post_button = st.button("Post")

        if post_button:
            if st.session_state.user is not None:
                # Create 'uploads' directory if it doesn't exist
                os.makedirs('uploads', exist_ok=True)
                video_url = None
                if video:
                    video_url = f"uploads/{st.session_state.user.username}_{video.name}"
                    with open(video_url, 'wb') as f:
                        f.write(video.read())
                add_post(st.session_state.user.username, title, content, video_url, visibility)
                st.success("Post created successfully!")
            else:
                st.warning("You need to be logged in to create a post.")

# Run the app
if __name__ == "__main__":
    main()
