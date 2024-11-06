from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from datetime import datetime
import bcrypt
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret_key"  # Kunci rahasia untuk session

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Koneksi ke MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["pinterest_clone"]

# Koleksi untuk pengguna, postingan, dan kategori
users_collection = db["users"]
posts_collection = db["posts"]
categories_collection = db["categories"]
login_logs_collection = db["login_logs"]
likes_collection = db["likes"]
comments_collection = db["comments"]
follows_collection = db["follows"]
profile_collection = db["profile"]

# Fungsi untuk inisialisasi database
def initialize_database():
    if categories_collection.count_documents({}) == 0:
        # Data contoh untuk koleksi kategori
        categories = [
            {"name": "Nature"},
            {"name": "Lifestyle"},
            {"name": "Sea"},
            {"name": "Food"},
            {"name": "Travel"},
            {"name": "Technology"},
            {"name": "Fashion"},
            {"name": "Art"},
            {"name": "Sports"},
            {"name": "Music"},
            {"name": "Education"},
            {"name": "Health"},
            {"name": "Fitness"},
            {"name": "Animals"},
            {"name": "History"},
            {"name": "Business"},
            {"name": "Gaming"},
            {"name": "Photography"},
            {"name": "DIY"},
            {"name": "Gardening"},
            {"name": "Hobbies"},
            {"name": "Events"}
        ]
        categories_collection.insert_many(categories)  # Menyisipkan semua kategori
        print("Database initialized with categories.")

    # Inisialisasi data pengguna
    if users_collection.count_documents({}) == 0:
        users = [
            {"username": "tes", "email": "tes@gmail.com", "password": bcrypt.hashpw("123".encode('utf-8'), bcrypt.gensalt()), "nickname": "Tes", "joined_at": datetime.now(), "profile_pic": "static/images/default.jpg", "bio": "", "likes_count": 0},
            {"username": "tes1", "email": "tes1@gmail.com", "password": bcrypt.hashpw("123".encode('utf-8'), bcrypt.gensalt()), "nickname": "Tes1", "joined_at": datetime.now(), "profile_pic": "static/images/default.jpg", "bio": "", "likes_count": 0},
            {"username": "tes2", "email": "tes2@gmail.com", "password": bcrypt.hashpw("123".encode('utf-8'), bcrypt.gensalt()), "nickname": "Tes2", "joined_at": datetime.now(), "profile_pic": "static/images/default.jpg", "bio": "", "likes_count": 0}
        ]
        users_collection.insert_many(users)
        print("Many user created.")

    # Inisialisasi data postingan
    if posts_collection.count_documents({}) == 0:
        posts = [
            {"user_id": "tes", "title": "Beautiful Nature", "description": "Nature is beautiful", "image_url": "static/uploads/1.jpg", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes", "title": "Fashionable", "description": "Lifestyle is good", "image_url": "static/uploads/2.jpg", "category_id": "Fashion", "created_at": datetime.now()},
            {"user_id": "tes", "title": "Art", "description": "Art is beautiful", "image_url": "static/uploads/3.jpg", "category_id": "Art", "created_at": datetime.now()},
            {"user_id": "tes1", "title": "Nature", "description": "Sea is beatiful", "image_url": "static/uploads/4.jpg", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes1", "title": "Art", "description": "Art is good", "image_url": "static/uploads/5.jpg", "category_id": "Art", "created_at": datetime.now()},
            {"user_id": "tes1", "title": "Nature", "description": "Nature is good", "image_url": "static/uploads/6.jpg", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes2", "title": "Nature", "description": "Nature is beautiful", "image_url": "static/uploads/7.jpg", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes2", "title": "Art", "description": "Art is beautiful", "image_url": "static/uploads/8.png", "category_id": "Art", "created_at": datetime.now()},
            {"user_id": "tes2", "title": "Nature", "description": "Nature is good", "image_url": "static/uploads/9.png", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes", "title": "Beautiful Nature", "description": "Nature is beautiful", "image_url": "static/uploads/10.jpg", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes1", "title": "Nature", "description": "Sea is beatiful", "image_url": "static/uploads/11.jpg", "category_id": "Nature", "created_at": datetime.now()},
            {"user_id": "tes2", "title": "Nature", "description": "Nature is good", "image_url": "static/uploads/12.jpg", "category_id": "Nature", "created_at": datetime.now()}
        ]
        posts_collection.insert_many(posts)  # Menyisipkan semua postingan
        print("Database initialized with posts.")

# Panggil fungsi inisialisasi
initialize_database()

# Fungsi untuk membuat pengguna baru
def create_user(username, email, password, nickname) :
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "nickname": nickname,
        "joined_at": datetime.now(),  # Simpan waktu registrasi
        "profile_pic": "static/images/default.jpg",  # Default profile picture: None (belum diunggah)
        "bio": "",  # Default bio: kosong
        "likes_count": 0   # Default following count: 0
    }
    users_collection.insert_one(user)
    
@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "username" not in session:
        return redirect(url_for("login"))
    
    # Menghapus akun dari koleksi pengguna
    users_collection.delete_one({"username": session["username"]})
    session.pop("username", None)  # Menghapus session

    flash("Account deleted successfully!", "success")
    return redirect(url_for("login"))


def get_likes_count(user_id):
    # hitung jumlah likes dari semua post user
    likes_count = db.posts.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total_likes": {"$sum": "$likes_count"}}}
    ])
    return likes_count

# Fungsi untuk memverifikasi pengguna
def verify_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        return user
    return None

def log_login_activity(username, successful):
    login_log = {
        "username": username,
        "login_time": datetime.now(),
        "ip_address": request.remote_addr,  # Mendapatkan alamat IP dari request
        "device": "desktop",  
        "location": None,  # Lokasi pengguna (opsional)
        "successful": successful,
        "login_method": "password"
    }
    login_logs_collection.insert_one(login_log)

# Route Home
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    
    page = int(request.args.get("page", 1))
    per_page = 20
    skip = (page - 1) * per_page
    
    posts = list(posts_collection.find().sort("created_at", DESCENDING).skip(skip).limit(per_page))
    categories = list(categories_collection.find())

    # Ambil data pengguna untuk menampilkan foto profil
    user = users_collection.find_one({"username": session["username"]})
    profile_data = profile_collection.find_one({"username": session["username"]})
    
    # Jika data profil ada, gunakan foto profil yang ada, jika tidak gunakan default
    profile_image_url = profile_data['profile_pic'] if profile_data else user.get('profile_pic', 'static/images/default.jpg')
    
    # Tambahkan informasi likes untuk setiap post
    for post in posts:
        post["_id"] = str(post["_id"])
        # Ambil semua likes untuk post ini
        post_likes = list(likes_collection.find({"post_id": post["_id"]}).sort("created_at", DESCENDING))
        post["likes_count"] = len(post_likes)
        
        # Cek like dari user current
        user_like = next((like for like in post_likes if like["user_id"] == session["username"]), None)
        post["is_liked"] = user_like is not None
        if user_like:
            post["liked_at"] = user_like["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        
        # Ambil 3 user terakhir yang like
        post["recent_likes"] = [{"user_id": like["user_id"], 
                               "liked_at": like["created_at"].strftime("%Y-%m-%d %H:%M:%S")} 
                              for like in post_likes[:3]]
        
        # Ambil comments, urutkan berdasarkan waktu terbaru
        post["comments"] = list(comments_collection.find({"post_id": post["_id"]}).sort("created_at", DESCENDING).limit(3))
    
    return render_template("home.html", 
                         username=session["username"],
                         posts=posts,
                         categories=categories,
                         profile_image_url=profile_image_url)



@app.route("/post/<post_id>/likes")
def post_likes(post_id):
    if "username" not in session:
        return redirect(url_for("login"))
        
    likes = list(likes_collection.find({"post_id": post_id}).sort("created_at", DESCENDING))
    likes_with_time = [{
        "user_id": like["user_id"],
        "liked_at": like["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    } for like in likes]
    
    return jsonify(likes_with_time)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Periksa apakah username sudah ada
        if users_collection.find_one({"username": username}):
            flash("Username already exists!", "error")
            return redirect(url_for("register"))

        # Set nickname dari username
        nickname = username
        
        # Set waktu pendaftaran
        created_at = datetime.now()

        # Fungsi create_user diubah agar menerima nickname dan created_at
        create_user(username, email, password, nickname)
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
        
    return render_template("register.html")

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = users_collection.find_one({'username': session['username']})
    profile_data = profile_collection.find_one({'username': session['username']})
    
    # Ambil nilai likes_count dari pengguna
    likes_count = user.get("likes_count", 0)
    
    if request.method == 'POST':
        # Mengunggah foto profil
        profile_pic = request.files['profile_pic']
        if profile_pic:
            profile_data = {
                'username': session['username'],
                'bio': request.form['bio'],
                'profile_pic': profile_pic.read()
            }
            profile_collection.replace_one({'username': session['username']}, profile_data, upsert=True)
    
    # Ambil postingan pengguna, diurutkan berdasarkan `created_at` secara menurun
    user_posts = list(posts_collection.find({"user_id": session['username']}).sort("created_at", DESCENDING))

    return render_template('profile.html', user=user, profile=profile_data, posts=user_posts, likes_count=likes_count)


@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Mencari post berdasarkan post_id
    post = posts_collection.find_one({'_id': ObjectId(post_id)})

    # Hitung jumlah like untuk postingan ini
    likes_count = likes_collection.count_documents({'post_id': post_id})

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        # Update judul dan deskripsi postingan di database
        posts_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {
                'title': title,
                'description': description
            }}
        )

        flash('Post updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_post.html', post=post, likes_count=likes_count)


@app.route("/create-post", methods=["GET", "POST"])
def create_post():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        image = request.files["image"]
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f"{app.config['UPLOAD_FOLDER']}/{filename}"
        else:
            image_url = None
        
        post = {
            "user_id": session["username"],
            "title": request.form["title"],
            "description": request.form["description"],
            "image_url": image_url,
            "category_id": request.form["category"],
            "created_at": datetime.now()  # Simpan sebagai objek datetime
        }
        posts_collection.insert_one(post)
        flash("Post created successfully!", "success")
        return redirect(url_for("home"))
    
    categories = list(categories_collection.find())
    return render_template("create_post.html", categories=categories)

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Hapus postingan dari koleksi posts
    result = posts_collection.delete_one({'_id': ObjectId(post_id)})

    if result.deleted_count == 1:
        flash('Post deleted successfully!', 'success')
    else:
        flash('Error deleting post.', 'error')

    return redirect(url_for('profile'))  # Redirect ke halaman profil atau halaman lain yang sesuai


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = users_collection.find_one({'username': session['username']})
    profile_data = profile_collection.find_one({'username': session['username']})

    if request.method == 'POST':
        username = session['username']
        bio = request.form.get('bio', '')

        # Check if a new profile picture is uploaded
        profile_pic = request.files.get('profile_pic')
        if profile_pic:
            filename = secure_filename(profile_pic.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(file_path)
            profile_pic_url = f"/{file_path}"
        else:
            profile_pic_url = profile_data['profile_pic'] if profile_data else "static/images/default.jpg"

        # Update profile in the database
        profile_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'bio': bio,
                    'profile_pic': profile_pic_url,
                    'updated_at': datetime.now()
                }
            },
            upsert=True
        )
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('update_profile.html', user=user, profile=profile_data)

@app.route("/search")
def search():
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    
    search_filters = {}
    if category:
        search_filters["category_id"] = category
    elif query:
        search_filters["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"tags": {"$regex": query, "$options": "i"}}
        ]

    posts = list(posts_collection.find(search_filters).sort("created_at", DESCENDING))

    for post in posts:
        post["_id"] = str(post["_id"])

    return jsonify({"posts": posts})

@app.route("/like/<post_id>", methods=["POST"])
def like_post(post_id):
    if "username" not in session:
        return jsonify({"error": "Please login first"}), 401
    
    user_id = session["username"]
    current_time = datetime.now()
    
    # Cek apakah postingan ada
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    post_owner_id = post["user_id"]  # ID pemilik postingan
    
    # Cek apakah pengguna sudah memberikan like pada postingan ini
    existing_like = likes_collection.find_one({
        "user_id": user_id,
        "post_id": post_id
    })
    
    response = {}
    
    if existing_like:
        # Jika sudah "like" sebelumnya, maka "unlike"
        likes_collection.delete_one({"_id": existing_like["_id"]})
        
        # Pastikan `likes_count` tidak menjadi negatif
        users_collection.update_one(
            {"username": post_owner_id, "likes_count": {"$gt": 0}},
            {"$inc": {"likes_count": -1}}
        )
        response["action"] = "unliked"
    else:
        # Jika belum "like", maka tambahkan "like" baru
        like = {
            "user_id": user_id,
            "post_id": post_id,
            "created_at": current_time 
        }
        likes_collection.insert_one(like)
        
        # Tambahkan `likes_count` hanya jika pengguna "like"
        users_collection.update_one(
            {"username": post_owner_id},
            {"$inc": {"likes_count": 1}}
        )
        response["action"] = "liked"
    
    # Hitung jumlah total likes untuk postingan ini
    response["likes_count"] = likes_collection.count_documents({"post_id": post_id})
    
    return jsonify(response)

@app.route("/comment/<post_id>", methods=["POST"])
def add_comment(post_id):
    if "username" not in session:
        return jsonify({"error": "Please login first"}), 401
    
    comment = {
        "user_id": session["username"],
        "post_id": post_id,
        "content": request.json["content"],
        "created_at": datetime.now()
    }
    
    comments_collection.insert_one(comment)
    return jsonify({"success": True})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = verify_user(username, password)
        if user:
            session["username"] = user["username"]
            log_login_activity(username, successful=True)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            log_login_activity(username, successful=False)
            flash("Invalid username or password!", "error")
            return redirect(url_for("login"))
    return render_template("login.html")



# Route Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)