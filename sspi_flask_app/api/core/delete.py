from ... import sspidb, sspi_metadata
from ..resources.utilities import lookup_database
from flask import Blueprint, redirect, render_template, request, flash, url_for
from flask_login import login_required
from wtforms import StringField
from bson.objectid import ObjectId
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


delete_bp = Blueprint("delete_bp", __name__,
                      template_folder="templates", 
                      static_folder="static", 
                      url_prefix="/delete")

db_choices = [""] + sspidb.list_collection_names()
ic_choices = [""] + sspi_metadata.indicator_codes()

class RemoveDuplicatesForm(FlaskForm):
    database = SelectField(choices = ["", "sspi_raw_api_data", "sspi_clean_api_data", "sspi_imputed_data"], validators=[DataRequired()], default="", label="Database")
    submit = SubmitField('Remove Duplicates')

class RemoveLooseDataForm(FlaskForm):
    database = SelectField(choices = ["", "sspi_raw_api_data", "sspi_clean_api_data", "sspi_imputed_data"], validators=[DataRequired()], default="", label="Database")
    submit = SubmitField('Remove Loose Data')

class DeleteIndicatorForm(FlaskForm):
    database = SelectField(choices = db_choices, validators=[DataRequired()], default="", label="Database")
    indicator_code = SelectField(choices = ic_choices, validators=[DataRequired()], default="---", label="Indicator Code")
    submit = SubmitField('Delete Indicator')

class ClearDatabaseForm(FlaskForm):
    database = StringField(validators=[DataRequired()], label="Database Name")
    database_confirm = StringField(validators=[DataRequired()], label="Confirm Database Name")
    submit = SubmitField('Clear Database')

@delete_bp.route('/')
@login_required
def get_delete_page():
    delete_indicator_form = DeleteIndicatorForm(request.form)
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    remove_loose_data_form = RemoveLooseDataForm(request.form)
    clear_database_form = ClearDatabaseForm(request.form)
    return render_template('delete-form.html', remove_duplicates_form=remove_duplicates_form, remove_loose_data_form=remove_loose_data_form, delete_indicator_form=delete_indicator_form, clear_database_form=clear_database_form)

@delete_bp.route("/indicator", methods=["POST"])
@login_required
def delete_indicator_data():
    delete_indicator_form = DeleteIndicatorForm(request.form)
    if delete_indicator_form.validate_on_submit():
        IndicatorCode = delete_indicator_form.indicator_code.data
        database = lookup_database(delete_indicator_form.database.data)
        count = database.delete_many({"IndicatorCode": IndicatorCode})
        flash(f"Deleted {count} observations of Indicator {IndicatorCode} from database {database.name}")
    return redirect(url_for('.get_delete_page'))

@delete_bp.route("/duplicates", methods=["POST"])
@login_required
def delete_duplicates():
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    database = lookup_database(request.form.get("database"))
    if remove_duplicates_form.validate_on_submit():
        count = database.drop_duplicates()
        flash("Found and deleted {0} duplicate observations from database {1}".format(count, database.name))
    return redirect(url_for(".get_delete_page"))

@delete_bp.route("/loose", methods=["POST"])
@login_required
def remove_loose_data():
    remove_loose_data_form = RemoveLooseDataForm(request.form)
    database = lookup_database(request.form.get("database"))
    if remove_loose_data_form.validate_on_submit():
        MongoQuery = {"IndicatorCode": {"$nin": indicator_codes()}}
        count = database.delete_many(MongoQuery)
        flash(f"Deleted {count} observations from database {database.name}")
    return redirect(url_for(".get_delete_page"))


@delete_bp.route("/clear", methods=["POST"])
@login_required
def clear_db():
    clear_database_form = ClearDatabaseForm(request.form)
    if clear_database_form.validate_on_submit():
        database = lookup_database(clear_database_form.database.data)
        if clear_database_form.database.data == clear_database_form.database_confirm.data:
            count = database.delete_many({})
            flash("Deleted {0} observations in clearing database {1}".format(count, database.name))
        else:
            flash("Database names do not match")
    return redirect(url_for(".get_delete_page"))
