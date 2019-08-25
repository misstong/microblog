from app import app,db
from flask import render_template
from datetime import datetime
import re
from app.forms import EditProfileForm,PostForm,SearchForm
from flask import flash, redirect, url_for
from flask_login import current_user,login_user ,logout_user,login_required
from app.models import User,Post
from flask import request
from werkzeug.urls import url_parse
from guess_language import guess_language
from flask import g
from flask_babel import get_locale
from flask import jsonify
from app.translate import translate

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page',1,type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page,app.config['POSTS_PER_PAGE'],False
    )
    next_url = url_for('user',username=user.username,page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user',username=user.username,page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html',user=user,posts=posts.items,next_url=next_url,prev_url=prev_url)

@app.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data 
        current_user.about_me = form.about_me.data 
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for('edit_profile'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',title="Edit Profile",form=form)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page,app.config['POSTS_PER_PAGE'],False
    )
    next_url = url_for('explore',page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore',page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html',title='Explore',posts=posts.items,next_url=next_url,prev_url=prev_url)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user',username=username))
    current_user.follow(user)
    db.session.commit()
    flash("You are following {}!".format(username))
    return redirect(url_for('user',username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first
    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Your cannot unfollow yourself!')
        return redirect(url_for('index'))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user',username=username))



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
        g.locale = str(get_locale())


@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ''
        post = Post(body=form.post.data,author=current_user,language=language)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@app.route("/hello/<name>")
def hello_there(name):
    now = datetime.now()
    formatted_now = now.strftime("%A, %d %B, %Y at %X")

    # Filter the name argument to letters only using regular expressions. URL arguments
    # can contain arbitrary text, so we restrict to safe characters only.
    match_object = re.match("[a-zA-Z]+", name)

    if match_object:
        clean_name = match_object.group(0)
    else:
        clean_name = "Friend"

    content = "Hello there, " + clean_name + "! It's " + formatted_now
    return content


@app.route('/search')
@login_required
def search():
    # if not g.search_form.validate():
    #     return redirect(url_for('explore'))
    page = request.args.get('page',1,type=1)
    posts,total = Post.search(g.search_form.q.data,page,app.config['POSTS_PER_PAGE'])
    next_url = url_for('search',q=g.search_form.q.data,page=page+1) \
        if total > page * app.config['POSTS_PER_PAGE'] else None 
    prev_url = url_for('search',q=g.search_form.q.data,page=page-1) \
        if page > 1 else None
    return render_template('search.html',title="Search",posts=posts,next_url=next_url,prev_url=prev_url)