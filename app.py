import os

from flask import Flask, flash, redirect, render_template, request, url_for
from cs50 import SQL
import db_init
import helpers
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pr-logger-vercel-secret")

if os.environ.get("VERCEL"):
    db_path = "/tmp/pr_logger.db"
else:
    db_path = "pr_logger.db"

db_init.init_db(db_path)
db = SQL(f"sqlite:///{db_path}")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    pr_logs = helpers.get_pr_logs(db)
    return render_template("index.html", pr_logs=pr_logs)

@app.route("/create_pr", methods=["GET", "POST"])
def create_pr():
    if request.method == "GET":
        new_pr_no = helpers.get_new_pr_no(db)
        creation = True
        return render_template("process_pr_form.html", new_pr_no=new_pr_no, creation=creation)

    pr_no, pr_title, pr_currency, pr_budget_line, pr_date, pr_total_cost = helpers.get_log_form_data()
    pr_indices, pr_descriptions, pr_costs, pr_quantities, pr_totals = helpers.get_entries_form_data(db)

    helpers.insert_pr_log(db, pr_no, pr_title, pr_currency, pr_budget_line, pr_date, pr_total_cost)
    pr_id = helpers.get_latest_pr_id(db)

    for i in range(len(pr_indices)):
        helpers.insert_pr_entry(db, pr_id, pr_indices[i], pr_descriptions[i], pr_costs[i], pr_quantities[i], pr_totals[i])

    flash(f"PR {pr_no} was created successfully.", "info")
    return redirect("/")

@app.route("/toggle_pr_status", methods=["POST"])
def toggle_pr_status():
    pr_no = request.form.get('pr-no')
    status = request.form.get('status')

    status_bool, status_text, message_style = helpers.get_status_details(status)
    helpers.update_pr_status(db, pr_no, status_bool)

    flash(f"PR {pr_no} has been {status_text} successfully.", message_style)
    return redirect("/")

@app.route("/view_pr")
def view_pr():
    pr_no = request.args.get('pr_no')
    max_pr_id = helpers.get_max_pr_id(db, pr_no)
    pr_log = helpers.get_pr_log(db, pr_no, max_pr_id)
    pr_entries = helpers.get_pr_entries(db, pr_no, max_pr_id)
    pr_revisions = helpers.get_pr_revisions(db, pr_no)
    return render_template("view_pr.html", pr_log=pr_log, pr_entries=pr_entries, pr_revisions=pr_revisions)

@app.route("/view_revision")
def view_revision():
    pr_id = request.args.get('pr-id')
    pr_no = helpers.get_pr_no(db, pr_id)
    pr_log = helpers.get_pr_log_by_id(db, pr_id)
    pr_entries = helpers.get_pr_entries_by_id(db, pr_id)
    pr_revisions = helpers.get_pr_revisions(db, pr_no)

    pr_log["revision"] = json.loads(pr_log["revision"])
    for entry in pr_entries:
        entry["revision"] = json.loads(entry["revision"])

    bool_revision = True
    return render_template("view_pr.html", bool_revision=bool_revision, pr_log=pr_log, pr_entries=pr_entries, pr_revisions=pr_revisions)

@app.route("/revise_pr")
def revise_pr():
    pr_no = request.args.get('pr_no')
    max_pr_id = helpers.get_max_pr_id(db, pr_no)
    pr_log = helpers.get_pr_log(db, pr_no, max_pr_id)
    pr_entries = helpers.get_pr_entries(db, pr_no, max_pr_id)
    return render_template("process_pr_form.html", pr_log=pr_log, pr_entries=pr_entries)

@app.route("/update_pr", methods=["POST"])
def update_pr():
    pr_no, pr_title, pr_currency, pr_budget_line, pr_date, pr_total_cost = helpers.get_log_form_data()
    pr_indices, pr_descriptions, pr_costs, pr_quantities, pr_totals = helpers.get_entries_form_data(db)

    current_pr_id = helpers.get_max_pr_id(db, pr_no)
    revised_pr_id = helpers.get_next_pr_id(db)

    current_pr_logs = helpers.get_pr_log_by_id(db, current_pr_id)
    current_pr_entries = helpers.get_pr_entries_by_id(db, current_pr_id)

    revised_pr_logs = {
        "budget_line": pr_budget_line,
        "creation_date": pr_date,
        "currency": pr_currency,
        "title": pr_title,
        "total_cost": float(pr_total_cost),
    }

    revised_pr_entries = []
    for i in range(len(pr_indices)):
        revised_pr_entry = {
            "cost": pr_costs[i],
            "description": pr_descriptions[i],
            "index": pr_indices[i],
            "quantity": pr_quantities[i],
            "total": pr_totals[i],
        }
        revised_pr_entries.append(revised_pr_entry)

    bool_change, log_change, entries_changes = helpers.detect_changes(db, current_pr_id, current_pr_logs, revised_pr_logs, current_pr_entries, revised_pr_entries)

    if not bool_change:
        flash("No changes detected, cannot submit revision.", "danger")
        return redirect(url_for('revise_pr', pr_no=pr_no))

    helpers.update_revisions(db, current_pr_id, log_change, entries_changes)

    helpers.insert_pr_log(db, pr_no, pr_title, pr_currency, pr_budget_line, pr_date, pr_total_cost)
    for i in range(len(pr_indices)):
        helpers.insert_pr_entry(db, revised_pr_id, pr_indices[i], pr_descriptions[i], pr_costs[i], pr_quantities[i], pr_totals[i])

    helpers.insert_pr_revision(db, current_pr_id)
    flash(f"PR {pr_no} was revised successfully.", "info")
    return redirect(url_for('view_pr', pr_no=pr_no))

@app.route("/cancel")
def cancel():
    flash("No changes were made.", "danger")
    return redirect("/")

if __name__ == "__main__":
    app.run()