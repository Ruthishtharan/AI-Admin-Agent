# AI Agent Prompt Guide

Ready-to-use prompts for the IT Admin Agent. Copy any of these directly into the CLI, Web Chat UI, or Slack bot.

---

## Basic User Management

### Create a User
```
Create a new user named Alice Chen with email alice.chen@company.com in the Engineering department
```
```
Add a new employee John Smith, email john.smith@company.com, role contractor, department Marketing
```
```
Create an admin user named David Kumar with email david.kumar@company.com and assign him Microsoft 365 E5 license
```

### Reset Password
```
Reset the password for john.doe@company.com
```
```
John Doe at john.doe@company.com forgot his password, please reset it
```
```
Reset passwords for both jane.smith@company.com and sarah.lee@company.com
```

### Disable / Enable Account
```
Disable the account for bob.johnson@company.com
```
```
Bob Johnson has left the company, disable his account at bob.johnson@company.com immediately
```
```
Re-enable the account for bob.johnson@company.com, he is rejoining the team
```

### Delete a User
```
Delete the user bob.johnson@company.com from the system
```
```
Permanently remove the account for sarah.lee@company.com
```

### Assign License or Role
```
Assign Microsoft 365 E3 license to john.doe@company.com
```
```
Upgrade jane.smith@company.com to Microsoft 365 E5 license
```
```
Change the role of john.doe@company.com to admin
```
```
Assign Google Workspace Business license to alice.chen@company.com and set her role to employee
```

---

## Multi-Step Tasks

### Check → Create → Assign (Conditional Logic)
```
Check if alice.chen@company.com exists in the system. If she does not exist, create her with the name Alice Chen, role employee, department Engineering, then assign her a Microsoft 365 E3 license. If she already exists, just assign the license.
```
```
Look up bob.johnson@company.com. If the account is inactive, enable it. If it is active, reset his password.
```
```
Check if david.kumar@company.com is in the system. If not, create him as an admin in the IT department with Microsoft 365 E5 license.
```

### Onboarding a New Employee
```
Onboard a new employee: full name Priya Patel, email priya.patel@company.com, role employee, department HR. Create the account and assign Microsoft 365 E1 license.
```
```
Set up a new contractor account for Mike Ross at mike.ross@company.com in the Legal department. Assign no license for now.
```

### Offboarding an Employee
```
Offboard sarah.lee@company.com — disable her account and reset her password so she cannot log back in
```
```
John Doe is leaving the company. Disable john.doe@company.com and make a note that the account has been deactivated.
```

### Batch Operations
```
Reset the passwords for john.doe@company.com and jane.smith@company.com one after the other
```
```
Check all users on the system and tell me how many are currently active
```

---

## Verification and Reporting

### Check User Status
```
Go to the users page and tell me the current status of bob.johnson@company.com
```
```
Look up jane.smith@company.com and tell me her current role, department, and license
```
```
Check the users list and tell me which users are currently inactive
```

### Audit
```
Go to the admin panel and give me a summary of how many total users exist and how many are active
```
```
List all users who have no license assigned
```

---

## Slack-Specific Prompts

Use these when messaging the Slack bot directly (DM or @mention):

```
@IT Admin Agent reset password for john.doe@company.com
```
```
@IT Admin Agent create user Alice Chen alice.chen@company.com Engineering employee Microsoft 365 E3
```
```
@IT Admin Agent check if priya.patel@company.com exists, if not create her as an employee in HR
```
```
@IT Admin Agent disable bob.johnson@company.com — he left the company today
```
```
@IT Admin Agent onboard new hire: name David Lee, email david.lee@company.com, department Finance, role employee
```

---

## SaaS Panel Prompts (saas_agent.py)

Use these when running against a real SaaS admin panel.

### HubSpot
```
Go to HubSpot contacts and create a new contact named Alice Chen with email alice.chen@company.com
```
```
Invite a new user with email david.kumar@company.com to the HubSpot workspace
```
```
Search for john.doe@company.com in HubSpot contacts and check if he exists
```

### Notion
```
Invite alice.chen@company.com as a member to the Notion workspace
```
```
Go to Notion settings and check how many members are currently in the workspace
```
```
Remove bob.johnson@company.com from the Notion workspace members list
```

### Google Workspace
```
Create a new user in Google Workspace admin: first name Alice, last name Chen, email alice.chen@yourdomain.com
```
```
Suspend the Google Workspace account for bob.johnson@yourdomain.com
```
```
Reset the password for john.doe@yourdomain.com in Google Workspace admin
```

---

## Power Prompts (Complex, Multi-Step)

These are the most advanced prompts that demonstrate the agent's full capability:

```
Check if alice.chen@company.com exists in the system.
If she does not exist:
  1. Create her with name Alice Chen, role employee, department Engineering
  2. Assign Microsoft 365 E3 license
  3. Confirm the account was created successfully
If she already exists:
  1. Check her current license
  2. If she has no license, assign Microsoft 365 E1
  3. Tell me what action was taken
```

```
Perform an IT audit:
1. Go to the users page
2. Count how many users are active and how many are inactive
3. Identify any users with no license assigned
4. Report back a full summary
```

```
Onboard three new employees one by one:
1. Alice Chen - alice.chen@company.com - Engineering - Microsoft 365 E3
2. David Lee - david.lee@company.com - Finance - Microsoft 365 E1
3. Priya Patel - priya.patel@company.com - HR - Google Workspace Basic
After creating each one, confirm it was successful before moving to the next.
```

```
Bob Johnson (bob.johnson@company.com) has rejoined the company as a full-time employee in Sales.
Enable his account, update his role from contractor to employee, and assign Microsoft 365 E3 license.
```

---

## Tips for Writing Your Own Prompts

| Do this | Example |
|---|---|
| Include full name and email | "named Alice Chen with email alice.chen@company.com" |
| Specify role clearly | "role employee / admin / contractor / guest" |
| Name the department | "in the Engineering department" |
| Name the license exactly | "Microsoft 365 E3" or "Google Workspace Basic" |
| Use conditional phrasing for logic | "if the user does not exist, create them, then..." |
| Chain steps naturally | "first reset the password, then disable the account" |

**Available roles:** `employee`, `admin`, `contractor`, `guest`

**Available licenses:**
- `None`
- `Microsoft 365 E1`
- `Microsoft 365 E3`
- `Microsoft 365 E5`
- `Google Workspace Basic`
- `Google Workspace Business`
