from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,TextAreaField
from wtforms.validators import DataRequired, ValidationError,Email,EqualTo,Length
from app.models import User
from flask import request

class EditProfileForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    about_me = TextAreaField('About me',validators=[Length(min=0,max=140)])
    submit = SubmitField('Submit')

    def __init__(self,orginal_username,*args,**kwargs):
        super(EditProfileForm,self).__init__(*args,**kwargs)
        self.orginal_username = orginal_username

    def validate_username(self,username):
        if username.data != self.orginal_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
    

class PostForm(FlaskForm):
    post = TextAreaField('Say something',validators=[
        DataRequired(),Length(min=1,max=140)
    ])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    q = StringField('Search',validators=[DataRequired()])

    def __init__(self,*args,**kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] =request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm,self).__init__(*args,**kwargs)

    
class MessageForm(FlaskForm):
    message = TextAreaField('Message',validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField('submit')