EC2 Ubuntu Linux Hardening — Top 5 Controls

A shell script that applies the 5 most important security hardening controls to a freshly provisioned AWS EC2 Ubuntu instance.

What is Linux Hardening?

Linux hardening is the process of configuring a server to reduce its attack surface — the number of ways an attacker could break in, escalate privileges, or disrupt the system. It involves tightening access controls, removing unnecessary exposure, and enabling protective mechanisms so the system is significantly harder to compromise.

Why It's Required
Cloud servers are exposed to the internet and constantly scanned by automated bots looking for weak configurations.
A single unpatched or misconfigured EC2 instance can become an entry point into your entire infrastructure.
Hardening doesn't make a system unhackable — it raises the cost and difficulty of an attack, and limits the damage if a breach does occur.
Many compliance frameworks (CIS, PCI-DSS, HIPAA, ISO 27001) require hardened baselines before systems can go into production.
The 5 Controls in This Script
#	Control	Definition	Why We Use It
1	System Updates	Installing the latest official OS and package patches.	Closes known security vulnerabilities before attackers can exploit them.
2	Firewall (UFW)	Software that controls which network connections are allowed in and out of the server.	Blocks all unwanted inbound traffic except what's explicitly allowed (e.g. SSH).
3	SSH Hardening	Configuration changes restricting how someone can remotely log into the server.	Disables root login and password login — only SSH key holders can access the server, with no password to guess or brute-force.
4	Fail2Ban (Brute-Force Protection)	A tool that monitors login attempts and automatically blocks IPs that repeatedly fail to authenticate.	Stops automated bots and attackers from repeatedly guessing SSH credentials.
5	Sensitive File Permissions	Strict access rules on critical system files (e.g. /etc/shadow).	Prevents unauthorized users from reading password hashes or modifying core configuration.

Together, these controls address the three most common attack paths:

Unpatched vulnerabilities → System updates
Unrestricted network access → Firewall + SSH hardening + Fail2Ban
Unauthorized file access → File permissions
