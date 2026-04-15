from flask import render_template, request, redirect, url_for, flash, jsonify

from app.models import (
    load_users,
    find_user,
    create_user as model_create_user,
    reset_password,
    disable_user,
    enable_user,
    delete_user,
    assign_license,
    assign_role,
    user_exists,
)


def register_routes(app):

    @app.route("/")
    def home():
        users = load_users()
        stats = {
            "total": len(users),
            "active": sum(1 for u in users if u.get("status") == "active"),
            "inactive": sum(1 for u in users if u.get("status") == "inactive"),
            "admins": sum(1 for u in users if u.get("role") == "admin"),
        }
        return render_template("dashboard.html", stats=stats, recent_users=users[-5:])

    @app.route("/users")
    def users():
        all_users = load_users()
        return render_template("users.html", users=all_users)

    @app.route("/create-user", methods=["GET", "POST"])
    def create_user():
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            name = request.form.get("name", "").strip()
            role = request.form.get("role", "employee")
            department = request.form.get("department", "").strip()
            license_type = request.form.get("license", "None")

            if not email or not name:
                flash("Email and name are required.", "danger")
                return render_template("create_user.html")

            if user_exists(email):
                flash(f"User {email} already exists.", "danger")
                return render_template("create_user.html")

            model_create_user(email, name, role, department, license_type)
            flash(f"User {name} ({email}) created successfully.", "success")
            return redirect(url_for("users"))

        return render_template("create_user.html")

    @app.route("/reset-password/<email>", methods=["GET", "POST"])
    def reset_password_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))

        if request.method == "POST":
            reset_password(email)
            flash(f"Password has been reset for {email}.", "success")
            return redirect(url_for("users"))

        return render_template("reset_password.html", user=user)

    @app.route("/disable-user/<email>", methods=["GET", "POST"])
    def disable_user_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))

        if request.method == "POST":
            disable_user(email)
            flash(f"User {email} has been disabled.", "success")
            return redirect(url_for("users"))

        return render_template(
            "confirm_action.html",
            user=user,
            action="Disable",
            action_url=url_for("disable_user_view", email=email),
            danger=True,
        )

    @app.route("/enable-user/<email>", methods=["GET", "POST"])
    def enable_user_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))

        if request.method == "POST":
            enable_user(email)
            flash(f"User {email} has been enabled.", "success")
            return redirect(url_for("users"))

        return render_template(
            "confirm_action.html",
            user=user,
            action="Enable",
            action_url=url_for("enable_user_view", email=email),
            danger=False,
        )

    @app.route("/delete-user/<email>", methods=["GET", "POST"])
    def delete_user_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))

        if request.method == "POST":
            delete_user(email)
            flash(f"User {email} has been deleted.", "success")
            return redirect(url_for("users"))

        return render_template(
            "confirm_action.html",
            user=user,
            action="Delete",
            action_url=url_for("delete_user_view", email=email),
            danger=True,
        )

    @app.route("/assign-license/<email>", methods=["GET", "POST"])
    def assign_license_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))

        if request.method == "POST":
            license_type = request.form.get("license", "None")
            role = request.form.get("role", user.get("role", "employee"))
            assign_license(email, license_type)
            assign_role(email, role)
            flash(f"Role and license updated for {email}.", "success")
            return redirect(url_for("users"))

        return render_template("assign_license.html", user=user)

    @app.route("/chat")
    def chat():
        return render_template("chat.html")

    @app.route("/api/chat", methods=["POST"])
    def chat_api():
        from agent.agent import run_agent

        data = request.get_json()
        if not data or not data.get("task"):
            return jsonify({"error": "No task provided"}), 400

        task = data["task"]
        steps = []

        def progress_callback(step, message):
            steps.append({"step": step, "message": str(message)})

        try:
            result = run_agent(task, progress_callback=progress_callback)
            return jsonify({"success": True, "result": result, "steps": steps})
        except Exception as e:
            return jsonify({"success": False, "error": str(e), "steps": steps}), 500

    @app.route("/api/users")
    def api_users():
        return jsonify(load_users())
