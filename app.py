from flask import Flask
from models import db
from config import Config # Import your new config class
from flask import render_template, request, redirect, url_for, flash
from models import db, Survey, Question, QuestionOption, Response, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # Load settings from config.py
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    login_manager.init_app(app)
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.route('/')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if user already exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already taken!')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        # If all good, hash and save
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Success! You can now log in.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Check if user exists first
        if not user:
            flash('No account found with that username. Please sign up!')
            return redirect(url_for('login'))
        
        # Then check the password
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect password. Please try again.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/survey/new', methods=['GET', 'POST'])
@login_required
def create_survey():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # 1. Create the Survey (User ID 1 for now)
        new_survey = Survey(title=title, user_id=current_user.id, description=description)
        db.session.add(new_survey)
        db.session.flush() # Gets the ID without ending the transaction

        # 2. Get the questions (assuming multiple questions possible)
        question_texts = request.form.getlist('questions[]')
        
        for i, q_text in enumerate(question_texts):
            if q_text.strip():
                new_q = Question(text=q_text, survey_id=new_survey.id)
                db.session.add(new_q)
                db.session.flush()

                # 3. Get options for THIS specific question
                # We use the index 'i' to match options to their question
                option_texts = request.form.getlist(f'options_{i}[]')
                for o_text in option_texts:
                    if o_text.strip():
                        new_opt = QuestionOption(option_text=o_text, question_id=new_q.id)
                        db.session.add(new_opt)

        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('create_survey.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # 1. Get surveys created by the logged-in user
    my_surveys = Survey.query.filter_by(user_id=current_user.id).order_by(Survey.created_at.desc()).all()
    
    # 2. Get surveys created by everyone else
    other_surveys = Survey.query.filter(Survey.user_id != current_user.id)\
        .options(joinedload(Survey.creator))\
        .order_by(Survey.created_at.desc()).all()
    
    return render_template('dashboard.html', my_surveys=my_surveys, other_surveys=other_surveys)

@app.route('/survey/<int:survey_id>')
def view_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    return render_template('view_survey.html', survey=survey)

@app.route('/survey/<int:survey_id>/submit', methods=['POST'])
@login_required
def submit_survey(survey_id):
    # The form will send question IDs as keys and option IDs as values
    for question in Question.query.filter_by(survey_id=survey_id).all():
        option_id = request.form.get(f'question_{question.id}')
        
        if option_id:
            new_response = Response(
                survey_id=survey_id,
                question_id=question.id,
                option_id=option_id,
                user_id = current_user.id if current_user.is_authenticated else None
            )
            db.session.add(new_response)
    
    db.session.commit()
    
    return redirect(url_for('thanks', survey_id=survey_id))

@app.route('/thanks/<int:survey_id>')
@login_required
def thanks(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    return render_template('survey_submitted.html', survey_title = survey.title)
@app.route('/survey/delete/<int:survey_id>', methods=['POST'])
@login_required
def delete_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    # Security: Ensure only the owner can delete
    if survey.user_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for('dashboard'))

    db.session.delete(survey)
    db.session.commit()
    flash(f"Survey '{survey.title}' has been deleted.")
    return redirect(url_for('dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    username = user_to_delete.username # Save name before deleting
    
    # Are you deleting yourself?
    if user_id == current_user.id:
        logout_user() 
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("Your account has been permanently deleted.")
        return redirect(url_for('register'))
    
    # Deleting someone else (Admin action)
    db.session.delete(user_to_delete)
    db.session.commit()
    
    flash(f"User {username} and all their data have been wiped.")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)