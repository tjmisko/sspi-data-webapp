from ... import sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_raw_api_data
from ..api import lookup_database
from flask import Blueprint, redirect, render_template, request, session, flash
from flask_login import login_required
from wtforms import StringField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


delete_bp = Blueprint("delete_bp", __name__,
                      template_folder="templates", 
                      static_folder="static", 
                      url_prefix="/delete")

class RemoveDuplicatesForm(FlaskForm):
    database = SelectField(choices = ["sspi_main_data_v3", "sspi_raw_api_data", "sspi_clean_api_data"], validators=[DataRequired()], default="sspi_raw_api_data", label="Database")
    indicator_code = SelectField(choices = ["BIODIV", "COALPW"], validators=[DataRequired()], default="None", label="Indicator Code")
    submit = SubmitField('Remove Duplicates')

class DeleteIndicatorForm(FlaskForm):
    database = SelectField(choices = ["sspi_main_data_v3", "sspi_raw_api_data", "sspi_clean_api_data"], validators=[DataRequired()], default="None", label="Database")
    indicator_code = SelectField(choices = ["BIODIV", "REDLST", "COALPW"], validators=[DataRequired()], default="None", label="Indicator Code")
    submit = SubmitField('Delete Indicator')

class ClearDatabaseForm(FlaskForm):
    database = StringField(validators=[DataRequired()], label="Database Name")
    database_confirm = StringField(validators=[DataRequired()], label="Confirm Database Name")
    submit = SubmitField('Clear Database')

@delete_bp.route('/')
def get_delete_page():
    delete_indicator_form = DeleteIndicatorForm(request.form)
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    clear_database_form = ClearDatabaseForm(request.form)
    return render_template('delete-form.html', remove_duplicates_form=remove_duplicates_form, delete_indicator_form=delete_indicator_form, clear_database_form=clear_database_form)


@delete_bp.route("/indicator", methods=["POST"])
@login_required
def delete_indicator_data():
    delete_indicator_form = DeleteIndicatorForm(request.form)
    if delete_indicator_form.validate_on_submit():
        IndicatorCode = delete_indicator_form.indicator_code.data
        if delete_indicator_form.database.data == "sspi_main_data_v3":
            count = sspi_main_data_v3.delete_many({"IndicatorCode": IndicatorCode}).deleted_count
        elif delete_indicator_form.database.data == "sspi_raw_api_data":
            count = sspi_raw_api_data.delete_many({"collection-info.RawDataDestination": IndicatorCode}).deleted_count
        elif delete_indicator_form.database.data == "sspi_clean_api_data":
            count = sspi_clean_api_data.delete_many({"IndicatorCode": IndicatorCode}).deleted_count
        flash("Deleted " + str(count) + " documents")
    return redirect("/api/v1/delete")

@delete_bp.route("/duplicates", methods=["POST"])
@login_required
def delete_duplicates():
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    database = request.form.get("database")
    IndicatorCode = request.form.get("indicator_code")
    return redirect("/api/v1/delete")

@delete_bp.route("/clear", methods=["POST"])
@login_required
def clear_db():
    clear_database_form = ClearDatabaseForm(request.form)
    if request.method == "POST" and clear_database_form.validate_on_submit():
        if clear_database_form.database.data == clear_database_form.database_confirm.data:
            lookup_database(clear_database_form.database.data).delete_many({})
            flash("Cleared database " + clear_database_form.database.data)
        else:
            flash("Database names do not match")
    return get_delete_page()

@delete_bp.route("test")
def red():
    print(delete_bp.endpoint)
    print(str(delete_bp))
    print(delete_bp.name)
    print(delete_bp.import_name)
    return "done"