import os
import markdown
from PIL import Image
from flask import Flask, redirect, render_template, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from flask_login import UserMixin, login_user, logout_user, login_required, LoginManager, current_user



app = Flask(__name__)

app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///portfolio.db'


db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

# ======== User Form ========
class UserForm(FlaskForm):
	user_name = StringField("User Name", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Log In")

# ======== Department Forms ========
class DepartmentForm(FlaskForm):
	department_name = StringField("Department Name", validators=[DataRequired()])
	description = TextAreaField("Description of the Department", validators=[DataRequired()])
	submit = SubmitField("Add New Department")

class UpdateDepartmentForm(FlaskForm):
	department_name = StringField("Department Name", validators=[DataRequired()])
	description = TextAreaField("Description of the Department", validators=[DataRequired()])
	submit = SubmitField("Update Department")

# ======== Device Forms ========
class DeviceForm(FlaskForm):
	device_name = StringField("Device Name", validators=[DataRequired()])
	description = TextAreaField("Description of the Device", validators=[DataRequired()])
	select_department = SelectField("Department", choices=[], validators=[DataRequired()])
	submit = SubmitField("Add New Device")

class UpdateDeviceForm(FlaskForm):
	device_name = StringField("Device Name", validators=[DataRequired()])
	description = TextAreaField("Description of the Device", validators=[DataRequired()])
	select_department = SelectField("Department", choices=[], validators=[DataRequired()])
	submit = SubmitField("Update Device")

# ======== Model Forms ========
class ModelForm(FlaskForm):
	model_name = StringField("Model Name", validators=[DataRequired()])
	description = TextAreaField("Description of the Model", validators=[DataRequired()])
	picture_file = FileField("Insert Image", validators=[FileAllowed(['jpg', 'png'])])
	submit = SubmitField("Add New Model")

class UpdateModelForm(FlaskForm):
	model_name = StringField("Model Name", validators=[DataRequired()])
	description = TextAreaField("Description of the Device", validators=[DataRequired()])
	submit = SubmitField("Update Model")


# ======== User Database Model ========
class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True) 
	user_name = db.Column(db.String(120), nullable=False, unique=True)
	password = db.Column(db.String(120), nullable=False)

	def __repr__(self):
		return f"User Name: {self.user_name}. Password: {self.password}"

# ======== Department Database Model ========
class Department(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	department_name = db.Column(db.String(100), nullable=False)
	description = db.Column(db.Text, nullable=False)  # New field for department description
	devices = db.relationship('Device', backref='department', lazy=True)
	
	def __repr__(self):
		return f"Department Name: {self.department_name}"

# ======== Device Database Model ========
class Device(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	device_name = db.Column(db.String(100), nullable=False)
	description = db.Column(db.Text, nullable=False)  # New field for device description
	department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
	models = db.relationship('Model', backref='device', lazy=True)

	def __repr__(self):
		return f"Device Name: {self.device_name}, Department_id : {self.department_id}"

# ======== Device Models Database Model ========
class Model(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	model_name = db.Column(db.String(100), nullable=False)
	description = db.Column(db.Text, nullable=False)  # New field for model description
	image_filename = db.Column(db.String(100), nullable=False, default='logo.png')
	device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
	
	def __repr__(self):
		return f"Model Name: {self.model_name}"

# ======== Application Routes ========
@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = UserForm()
	if form.validate_on_submit():
		user = User.query.filter_by(user_name=form.user_name.data).first()
		if user:
			if user.password == form.password.data:
				login_user(user)
				flash("You are logged in successfuly", "success")
				return redirect(url_for('dashboard'))
			else:
				flash("Wrong Password. Please try again!", "danger")
				return redirect(url_for('login'))
		else:
			flash("Wrong Username. Please try again!", "danger")
			return redirect(url_for('login'))
		
	return render_template('/login.html', form=form)

@app.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
	logout_user()
	flash("You are logged out!", "warning")
	return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    departments = Department.query.all()  # Fetch all departments
    devices = Device.query.all()          # Fetch all devices
    models = Model.query.all()            # Fetch all models
    return render_template('dashboard.html', departments=departments, devices=devices, models=models)

# --------------All Departments Routes----------------
@app.route('/departments')
def departments():
	departments = Department.query.all()
	image_filename = 'logo.png'
	if departments:
		if departments[0].devices:
			if departments[0].devices[0].models:
				image_filename = departments[0].devices[0].models[0].image_filename

	return render_template("departments.html", departments=departments, image_filename=image_filename)

@app.route('/add_department', methods=["GET", "POST"])
def add_department():
	form = DepartmentForm()
	if form.validate_on_submit():
		department = Department(department_name=form.department_name.data, description=form.description.data)
		db.session.add(department)
		db.session.commit()
		return redirect(url_for('departments'))
	return render_template("add_department.html", form=form)

@app.route('/update_department/<int:id>', methods=["GET", "POST"])
def update_department(id):
	department_to_update = Department.query.get_or_404(id)
	form = UpdateDepartmentForm(department_name=department_to_update.department_name, description=department_to_update.description)
	
	if form.validate_on_submit():
		department_to_update.department_name=form.department_name.data
		department_to_update.description=form.description.data
		db.session.add(department_to_update)
		db.session.commit()
		flash("Department updated!", "primary")
		return redirect(url_for('departments'))
	return render_template("update_department.html", form=form)


@app.route('/delete_department/<int:id>', methods=["GET", "POST"])
def delete_department(id):
	department_to_delete = Department.query.get_or_404(id)
	devices_of_department = department_to_delete.devices
	for device in devices_of_department:
		models_of_device = device.models
		for model in models_of_device:
			db.session.delete(model)
			flash(f"{model.model_name} model deleted!", "info")
		db.session.delete(device)
		flash(f"{device.device_name} device deleted!", "info")
	db.session.delete(department_to_delete)
	flash(f"{department_to_delete.department_name} department deleted!", "info")
	db.session.commit()
	return redirect(url_for('departments'))

@app.route('/show_department/<int:id>')
def show_department(id):
	department_to_show = Department.query.get_or_404(id)
	if department_to_show:
		department_to_show.description = markdown.markdown(department_to_show.description)
	image_filename = 'logo.png'
	if department_to_show.devices:
		if department_to_show.devices[0].models:
			image_filename = department_to_show.devices[0].models[0].image_filename


	return render_template("show_department.html", department_to_show=department_to_show, image_filename=image_filename)

# --------------All Devices Routes----------------
@app.route('/devices')
def devices():
	devices = Device.query.all()
	image_filename = 'logo.png'
	if devices:
		if devices[0].models:
			image_filename =devices[0].models[0].image_filename

	return render_template("devices.html", devices=devices, image_filename=image_filename)


@app.route('/add_device', methods=["GET", "POST"])
def add_device():
	form =DeviceForm()
	departments= Department.query.all() #retrevie all departments
	if not departments:
		flash("You must add department first to add device!", "warning")
		return redirect(url_for('add_department'))
	for department in departments:
		select_department = (department.id, department.department_name) # make a tuple from departments database
		form.select_department.choices.append(select_department) # append it to the list of choises to select menu

	if form.validate_on_submit():
		device = Device(device_name=form.device_name.data, description=form.description.data, department_id=form.select_department.data)
		db.session.add(device)
		db.session.commit()
		return redirect(url_for('devices'))
	return render_template("add_device.html", form=form, departments=departments)

@app.route('/update_device/<int:id>', methods=["GET", "POST"])
def update_device(id):
	device_to_update = Device.query.get_or_404(id)
	form = UpdateDeviceForm(device_name=device_to_update.device_name, description=device_to_update.description, select_department=device_to_update.department_id)
	departments = Department.query.all()
	for department in departments:
		select_department = (department.id, department.department_name)
		form.select_department.choices.append(select_department)

	if form.validate_on_submit():
		device_to_update.device_name = form.device_name.data
		device_to_update.description = form.description.data
		device_to_update.department_id = form.select_department.data
		db.session.add(device_to_update)
		db.session.commit()
		flash("Device updated!", "primary")
		return redirect(url_for('devices'))
	return render_template("update_device.html", form=form)

@app.route('/delete_device/<int:id>', methods=["GET", "POST"])
def delete_device(id):
	device_to_delete = Device.query.get_or_404(id)
	models_of_device = device_to_delete.models
	for model in models_of_device:
		db.session.delete(model)
		flash(f"{model.model_name} model deleted!", "info")
	db.session.delete(device_to_delete)
	db.session.commit()
	flash(f"{device_to_delete.device_name} device deleted!", "info")
	return redirect(url_for('devices'))

@app.route('/show_device/<int:id>')
def show_device(id):
	device_to_show = Device.query.get_or_404(id)
	return render_template("show_dvice.html", device_to_show=device_to_show)

# --------------All Models Routes--------------------
@app.route('/add_model/<int:device_id>', methods=["GET", "POST"])
def add_model(device_id):
	form = ModelForm()
	device_of_model = Device.query.filter_by(id=device_id).first() #retrevie all devices
	image_filename = 'logo.png'
	if form.validate_on_submit():
		if form.picture_file.data:
			image_filename = form.picture_file.data.filename
			image_path = os.path.join(app.root_path, 'static/images', image_filename)
			print(image_path)
			form.picture_file.data.save(image_path)

			img = Image.open(image_path)
			img = img.resize((550, 600), Image.LANCZOS)  # Resize the image
			img.save(image_path)  # Save the resized image back to the same path

		model = Model(model_name=form.model_name.data, description=form.description.data, device_id=device_id, image_filename=image_filename)
		db.session.add(model)
		db.session.commit()
		return redirect(url_for('show_device', id=device_id))
	return render_template("add_model.html", form=form, device_of_model=device_of_model)

@app.route('/update_model/<int:id>', methods=["GET", "POST"])
def update_model(id):
	model_to_update = Model.query.filter_by(id=id).first()
	device_of_model = Device.query.filter_by(id=model_to_update.device_id).first()
	form =UpdateModelForm(model_name=model_to_update.model_name, description=model_to_update.description)
	if form.validate_on_submit():
		model_to_update.model_name = form.model_name.data
		model_to_update.decription = form.description.data
		#change image
		db.session.add(model_to_update)
		db.session.commit()
		return redirect(url_for('show_device',id=device_of_model.id))
	
	return render_template("update_model.html", form=form, device_of_model=device_of_model)


@app.route('/delete_model/<int:id>')
def delete_model(id):
		model_to_delete = Model.query.filter_by(id=id).first()
		device_of_model = Device.query.filter_by(id=model_to_delete.device_id).first()
		db.session.delete(model_to_delete)
		db.session.commit()
		flash(f"{model_to_delete.model_name} model deleted!", "info")
		return redirect(url_for('show_device',id=device_of_model.id))


@app.route('/show_model/<int:id>')
def show_model(id):
		model_to_show = Model.query.filter_by(id=id).first()
		
		return render_template('show_model.html', model_to_show=model_to_show)


		



#-------------------About Route-----------------------
@app.route('/about')
def about():
	return render_template("about.html")


if __name__ == "__main__":
	app.run(debug=True)