import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask import current_app as app
from flask_login import login_required

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from sspi_flask_app.api.resources.utilities import lookup_database
from sspi_flask_app.models.database import sspi_metadata, sspi_raw_api_data, sspidb

delete_bp = Blueprint(
    "delete_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/delete"
)


def sort_db(choice):
    if choice == "sspi_raw_api_data":
        return 0
    elif choice == "sspi_clean_api_data":
        return 1
    else:
        return 2


db_choices_ordered = sorted(
    sspidb.list_collection_names(),
    key=sort_db
)
db_choices = [""] + db_choices_ordered
ic_choices = [""] + sspi_metadata.indicator_codes()


class RemoveDuplicatesForm(FlaskForm):
    database = SelectField(choices=["", "sspi_raw_api_data", "sspi_clean_api_data", "sspi_imputed_data"], validators=[
                           DataRequired()], default="", label="Database")
    submit = SubmitField('Remove Duplicates')


class RemoveLooseDataForm(FlaskForm):
    database = SelectField(choices=["", "sspi_raw_api_data", "sspi_clean_api_data", "sspi_imputed_data"], validators=[
                           DataRequired()], default="", label="Database")
    submit = SubmitField('Remove Loose Data')


class DeleteIndicatorForm(FlaskForm):
    database = SelectField(choices=db_choices, validators=[
                           DataRequired()], default="", label="Database")
    indicator_code = SelectField(choices=ic_choices, validators=[
                                 DataRequired()], default="---", label="Indicator Code")
    submit = SubmitField('Delete Indicator')


class ClearDatabaseForm(FlaskForm):
    database = StringField(validators=[DataRequired()], label="Database Name")
    database_confirm = StringField(
        validators=[DataRequired()], label="Confirm Database Name")
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
        message_1 = f"Deleted {count} observations of Indicator"
        message_2 = f"{IndicatorCode} from database {database.name}"
        app.logger.info(message_1 + message_2)
        flash(message_1 + message_2)
    return redirect(url_for('.get_delete_page'))


@delete_bp.route("/duplicates", methods=["POST"])
@login_required
def delete_duplicates():
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    database = lookup_database(request.form.get("database"))
    if remove_duplicates_form.validate_on_submit():
        count = database.drop_duplicates()
        msg = (
            f"Found and deleted {count} duplicate observations "
            f"from database {database.name}"
        )
        app.logger.info(msg)
        flash(msg)
    return redirect(url_for(".get_delete_page"))


@delete_bp.route("/loose", methods=["POST"])
@login_required
def remove_loose_data():
    remove_loose_data_form = RemoveLooseDataForm(request.form)
    database = lookup_database(request.form.get("database"))
    indicator_codes = sspi_metadata.indicator_codes()
    if remove_loose_data_form.validate_on_submit():
        MongoQuery = {"IndicatorCode": {"$nin": indicator_codes}}
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
            msg = f"Deleted {count} observations clearing database {database}"
            app.logger.info(msg)
            flash(msg)
        else:
            flash("Database names do not match")
    return redirect(url_for(".get_delete_page"))


@delete_bp.route("/series/<database_name>/<series_code>", methods=["DELETE"])
@login_required
def delete_series(database_name, series_code):
    database = lookup_database(database_name)
    dataset_codes = sspi_metadata.get_dataset_dependencies(series_code)
    if database_name == "sspi_raw_api_data":
        message = ""
        for ds in dataset_codes:
            message += delete_raw_data(ds) + "\n"
    else:
        match = re.match("^[A-Za-z0-9_]+$", series_code)
        if not match:
            return "SeriesCode may contain only letters, numbers, and underscores"
        dataset_codes = sspi_metadata.get_dataset_dependencies(series_code)
        indicator_codes = sspi_metadata.get_indicator_dependencies(series_code)
        print(indicator_codes)
        delete_query = {
            "$or": [
                { "ItemCode": series_code },
                { "IndicatorCode": {"$in": indicator_codes } },
                { "DatasetCode": {"$in": dataset_codes }  }
            ]
        }
        count = database.delete_many(delete_query)
        message = f"Deleted {count} observations of SeriesCode {series_code} from Database {database.name}"
        app.logger.info(message)
    return message


@delete_bp.route("/indicator/<database_name>/<IndicatorCode>", methods=["DELETE"])
@login_required
def delete_database_indicator(database_name, IndicatorCode):
    database = lookup_database(database_name)
    count = database.delete_many({"IndicatorCode": IndicatorCode})
    message = (
        f"Deleted {count} observations of Indicator "
        f"{IndicatorCode} from database {database.name}"
    )
    app.logger.info(message)
    return message


@delete_bp.route("/clear/<database_name>", methods=["DELETE"])
@login_required
def delete_clear_database(database_name):
    database = lookup_database(database_name)
    # Dump a temporary copy to the system's temporary directory
    temp_dir = tempfile.gettempdir()
    timestr = datetime.now().strftime("%s")
    temp_file_path = os.path.join(temp_dir, f"{timestr}_{database_name}.json")
    with open(temp_file_path, 'w') as temp_file:
        json.dump(list(database.find({})), temp_file)
    count = database.delete_many({})
    msg = (
        f"Deleted {count} observations from database {database.name}\n"
        f"Temporary copy saved to {temp_file_path}"
    )
    app.logger.info(msg)
    return msg

@delete_bp.route("/loose/<database_name>", methods=["DELETE"])
@login_required
def delete_loose_data(database_name):
    database = lookup_database(database_name)
    if database.name == "sspi_raw_api_data":
        query = {"$nor": []}
        dataset_codes = sspi_metadata.dataset_codes()
        for dsc in dataset_codes:
            source_info = sspi_metadata.get_source_info(dsc)
            query_line = sspi_raw_api_data.build_source_query(source_info)
            query["$nor"].append(query_line)
        if len(query["$nor"]) > 0:
            count = sspi_raw_api_data.delete_many(query)
            return f"Deleted {count} loose observations from {database.name}"
        return "No loose observations found in this database"
    else:
        return "Not implemented for this database type"
    count = database.delete_many(MongoQuery)
    msg = f"Deleted {count} loose observations from database {database.name}"
    app.logger.info(msg)
    return msg

@delete_bp.route("/raw/<raw_delete_code>", methods=["DELETE"])
@login_required
def delete_raw_data(raw_delete_code):
    if ":" in raw_delete_code:
        split_list = raw_delete_code.split(":")
        organization_code = split_list[0]
        query_code = split_list[1]
        query = {
            "Source.OrganizationCode": organization_code,
            "Source.QueryCode": query_code
        }
        count = sspi_raw_api_data.delete_many(query)
        msg = f"Deleted {count} raw API data for {query}"
        return msg
    elif raw_delete_code in sspi_metadata.dataset_codes():
        dataset_code = raw_delete_code.upper()
        source_info = sspi_metadata.get_source_info(dataset_code)
        query = sspi_raw_api_data.build_source_query(source_info)
        count = sspi_raw_api_data.delete_many(query)
        msg = f"Deleted {count} raw API data for {dataset_code}"
        app.logger.info(msg)
        return msg
    else:
        return (
            "Invalid raw_delete_code format. Use "
            "'OrganizationCode:QueryCode' or a valid DatasetCode."
        )
