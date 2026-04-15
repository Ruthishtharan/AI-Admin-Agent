# AI Agent Prompt Guide

50 ready-to-use prompts for the IT Admin Agent — from simple one-liners to complex multi-step workflows. Copy any prompt directly into the CLI, Web Chat UI, or Slack bot.

---

## 1. Create a New User
```
Create a new user named Alice Chen with email alice.chen@company.com in the Engineering department
```

## 2. Create a Contractor Account
```
Add a new contractor named Mike Ross with email mike.ross@company.com in the Legal department, no license needed for now
```

## 3. Create an Admin User with License
```
Create an admin user named David Kumar with email david.kumar@company.com in the IT department and assign him Microsoft 365 E5 license
```

## 4. Create a Guest Account
```
Set up a guest account for the external auditor Tom Gray at tom.gray@external.com with no license assigned
```

## 5. Reset a Password
```
Reset the password for john.doe@company.com
```

## 6. Reset Password with Context
```
John Doe locked himself out — please reset the password for john.doe@company.com so he can get back in
```

## 7. Reset Multiple Passwords
```
Reset the passwords for john.doe@company.com and jane.smith@company.com one after the other
```

## 8. Disable an Account
```
Disable the account for bob.johnson@company.com
```

## 9. Disable Account (Offboarding Reason)
```
Bob Johnson has left the company today — disable his account at bob.johnson@company.com immediately
```

## 10. Enable a Disabled Account
```
Re-enable the account for bob.johnson@company.com, he is rejoining the team next Monday
```

## 11. Delete a User
```
Delete the user sarah.lee@company.com from the system permanently
```

## 12. Assign a License
```
Assign Microsoft 365 E3 license to john.doe@company.com
```

## 13. Upgrade a License
```
Upgrade jane.smith@company.com from Microsoft 365 E1 to Microsoft 365 E5 license
```

## 14. Remove a License
```
Remove the license from bob.johnson@company.com and set it to None
```

## 15. Change a User's Role
```
Change the role of john.doe@company.com from employee to admin
```

## 16. Change Role and License Together
```
Set alice.chen@company.com role to contractor and assign Google Workspace Basic license
```

## 17. Check If a User Exists
```
Check if priya.patel@company.com exists in the system and tell me her current status
```

## 18. Look Up a User's Details
```
Look up jane.smith@company.com and tell me her current role, department, and license
```

## 19. Find Inactive Users
```
Go to the users list and tell me which accounts are currently inactive
```

## 20. Count All Users
```
Go to the admin panel dashboard and tell me how many total users are in the system
```

## 21. Onboard a New Employee (Full Flow)
```
Onboard a new employee — full name Priya Patel, email priya.patel@company.com, role employee, department HR. Create the account and assign Microsoft 365 E1 license.
```

## 22. Onboard a Senior Hire
```
Onboard a new senior engineer: name Raj Mehta, email raj.mehta@company.com, department Engineering, role employee, license Microsoft 365 E5
```

## 23. Offboard an Employee (Disable + Reset)
```
Sarah Lee is leaving the company. Disable her account at sarah.lee@company.com and reset her password so she cannot log back in
```

## 24. Offboard and Delete
```
John Doe has officially left. Disable john.doe@company.com first to confirm, then delete the account entirely
```

## 25. Conditional — Create If Not Exists
```
Check if alice.chen@company.com exists. If she does not exist, create her with name Alice Chen, role employee, department Engineering, and assign Microsoft 365 E3 license
```

## 26. Conditional — Create or Update
```
Check if david.kumar@company.com exists in the system. If he does not exist, create him as an admin in the IT department with Microsoft 365 E5 license. If he already exists, just make sure his role is set to admin.
```

## 27. Conditional — Enable or Reset
```
Look up bob.johnson@company.com. If the account is inactive, enable it. If it is already active, reset his password instead.
```

## 28. Conditional — License Check and Assign
```
Check alice.chen@company.com in the system. If she has no license assigned, give her Microsoft 365 E1. If she already has a license, leave it as is and just tell me what she has.
```

## 29. Conditional — Full Onboarding with Existence Check
```
Check if mike.ross@company.com already exists.
If he does not exist: create him as a contractor in the Legal department with no license, then report back that the account is ready.
If he already exists: check his current status, enable the account if it is disabled, and report his details.
```

## 30. Batch Onboard Multiple Users
```
Create the following three new employees one by one and confirm each before moving to the next:
1. Alice Chen — alice.chen@company.com — Engineering — employee — Microsoft 365 E3
2. David Lee — david.lee@company.com — Finance — employee — Microsoft 365 E1
3. Priya Patel — priya.patel@company.com — HR — employee — Google Workspace Basic
```

## 31. Batch Disable Multiple Accounts
```
Disable all of these accounts — they are from employees who left today:
bob.johnson@company.com and sarah.lee@company.com
```

## 32. Batch Password Reset
```
The Engineering team needs password resets. Reset passwords for john.doe@company.com and alice.chen@company.com back to back
```

## 33. Rehire Flow
```
Bob Johnson is rejoining the company as a full-time employee in Sales. Enable his account at bob.johnson@company.com, update his role from contractor to employee, and assign Microsoft 365 E3 license
```

## 34. Role Promotion
```
Jane Smith has been promoted to IT Admin. Update jane.smith@company.com role to admin and upgrade her license to Microsoft 365 E5
```

## 35. Department Transfer
```
John Doe is moving from Engineering to the Product team. Update his account john.doe@company.com — change his department to Product and upgrade his license to Microsoft 365 E5
```

## 36. Security Lockdown
```
Security alert — immediately disable the account for bob.johnson@company.com and reset the password to prevent any further access
```

## 37. Audit Report
```
Perform a full IT audit:
1. Go to the users page
2. Count how many users are active and how many are inactive
3. Identify any users with no license assigned
4. Give me a complete summary of the current state
```

## 38. License Audit
```
Go to the users list and check every user. Tell me which users do not have any license assigned and which license each active user currently holds
```

## 39. Admin Audit
```
Check the users list and tell me which accounts have the admin role — list all of them with their emails and departments
```

## 40. New Intern Setup
```
Set up an intern account for the summer — name Tom Gray, email tom.gray@company.com, role guest, department Engineering, no license needed. The account should be active and ready to go.
```

## 41. Create and Immediately Disable (Pre-provisioning)
```
Pre-provision an account for a new hire who starts next week — name Emma Wilson, email emma.wilson@company.com, role employee, department Marketing, Microsoft 365 E1. Create the account but then disable it so it stays inactive until she starts.
```

## 42. Verify Account Before Meeting
```
Before my 3pm meeting I need to confirm — check if alice.chen@company.com exists, is active, and has a license assigned. Give me a quick status report.
```

## 43. Fix a Broken Account
```
Something is wrong with john.doe@company.com — enable the account if it is disabled, reset the password, and confirm the account is active and ready for use
```

## 44. Contractor to Full-Time Conversion
```
Mike Ross has converted from contractor to full-time employee. Update mike.ross@company.com — change role from contractor to employee, department stays Legal, and assign Microsoft 365 E3 license
```

## 45. Quick User Lookup
```
Quick check — is sarah.lee@company.com active or inactive right now?
```

## 46. Full New Hire Checklist
```
New hire checklist for Raj Mehta joining Monday:
1. Create account: raj.mehta@company.com, role employee, department Engineering
2. Assign Microsoft 365 E3 license
3. Confirm the account shows as active
4. Report back when all steps are complete
```

## 47. Slack — Quick Password Reset
```
reset password for john.doe@company.com
```

## 48. Slack — Onboard New Hire
```
onboard new hire: name Alice Chen, email alice.chen@company.com, department Engineering, role employee, license Microsoft 365 E3
```

## 49. Slack — Conditional Create
```
check if priya.patel@company.com exists, if not create her as an employee in HR with Microsoft 365 E1 license
```

## 50. Slack — Offboard Immediately
```
urgent: disable bob.johnson@company.com right now, he left the company
```

---

## Tips for Writing Your Own Prompts

| Do this | Example |
|---|---|
| Always include full name and email | `named Alice Chen with email alice.chen@company.com` |
| Specify the role | `role employee / admin / contractor / guest` |
| Name the department | `in the Engineering department` |
| Use exact license names | `Microsoft 365 E3` or `Google Workspace Basic` |
| Use if/else for conditional tasks | `if the user does not exist, create them, then...` |
| Chain steps with numbers | `1. create the account 2. assign license 3. confirm` |
| Add urgency context when needed | `urgent:` or `immediately` makes the intent clear |
| Ask for confirmation at the end | `report back when all steps are complete` |

---

## Quick Reference

**Available Roles**
`employee` · `admin` · `contractor` · `guest`

**Available Licenses**
`None` · `Microsoft 365 E1` · `Microsoft 365 E3` · `Microsoft 365 E5` · `Google Workspace Basic` · `Google Workspace Business`

**Run modes**
- CLI → `python3 main.py`
- Web UI → `http://localhost:5000/chat`
- Slack → `python3 slack_bot.py`
- SaaS → `python3 saas_agent.py`
