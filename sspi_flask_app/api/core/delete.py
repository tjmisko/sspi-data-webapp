from flask import redirect, render_template, request, url_for
from flask_login import login_required
from wtforms import StringField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from ..api import lookup_database


class RemoveDuplicatesForm(FlaskForm):
    database = SelectField(choices = ["sspi_main_data_v3", "sspi_raw_api_data", "sspi_clean_api_data"], validators=[DataRequired()], default="sspi_raw_api_data", label="Database")
    indicator_code = SelectField(choices = ["BIODIV", "COALPW"], validators=[DataRequired()], default="None", label="Indicator Code")
    submit = SubmitField('Remove Duplicates')

class DeleteIndicatorForm(FlaskForm):
    database = SelectField(choices = ["sspi_main_data_v3", "sspi_raw_api_data", "sspi_clean_api_data"], validators=[DataRequired()], default="sspi_main_data_v3", label="Database")
    indicator_code = SelectField(choices = ["BIODIV", "REDLST", "COALPW"], validators=[DataRequired()], default="None", label="Indicator Code")
    submit = SubmitField('Delete')

class ClearDatabaseForm(FlaskForm):
    database = StringField(validators=[DataRequired()], label="Database Name")
    database_confirm = StringField(validators=[DataRequired()], label="Confirm Database Name")
    submit = SubmitField('Clear Database')

@delete_bp.route("/", methods=["GET", "POST"])
@login_required
def delete():
    delete_indicator_form = DeleteIndicatorForm(request.form)
    if request.method == "POST" and delete_indicator_form.validate_on_submit():
        IndicatorCode = delete_indicator_form.indicator_code.data
        if delete_indicator_form.database.data == "sspi_main_data_v3":
            count = sspi_main_data_v3.delete_many({"IndicatorCode": IndicatorCode}).deleted_count
        elif delete_indicator_form.database.data == "sspi_raw_api_data":
            count = sspi_raw_api_data.delete_many({"collection-info.RawDataDestination": IndicatorCode}).deleted_count
        elif delete_indicator_form.database.data == "sspi_clean_api_data":
            count = sspi_clean_api_data.delete_many({"IndicatorCode": IndicatorCode}).deleted_count
        flash("Deleted " + str(count) + " documents")

@delete_bp.route("/duplicates", methods=["POST"])
def remove_duplicates():
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    database = request.form.get("database")
    IndicatorCode = request.form.get("indicator_code")
    print(database, IndicatorCode)
    return redirect(url_for("api_bp.delete"))

@delete_bp.route("clear")
def delete():
    clear_database_form = ClearDatabaseForm(request.form)
    if request.method == "POST" and clear_database_form.validate_on_submit():
        if clear_database_form.database.data == clear_database_form.database_confirm.data:
            lookup_database(clear_database_form.database.data).delete_many({})
            flash("Cleared database " + clear_database_form.database.data)
        else:
            flash("Database names do not match")
    return render_template('api-delete-page.html', remove_duplicates_form=remove_duplicates_form, delete_indicator_form=delete_indicator_form, messages=get_flashed_messages(), clear_database_form=clear_database_form)
