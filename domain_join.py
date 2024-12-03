import os
import sys
import subprocess
import getpass

def install_packages():
    try:
        subprocess.run(["apt", "update"], check=True)
        subprocess.run(["apt", "install", "-y", "sssd-ad", "sssd-tools", "realmd", "adcli", "krb5-user", "sssd-krb5"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def configure_kerberos(domain):
    try:
        with open("/etc/krb5.conf", "w") as krb5_conf:
            krb5_conf.write(f"[libdefaults]\n\tdefault_realm = {domain.upper()}\n\trdns = false\n")
    except IOError as e:
        print(f"Error writing to /etc/krb5.conf: {e}")
        sys.exit(1)

def set_hostname(domain):
    try:
        hostname = subprocess.check_output("hostname", shell=True).strip().decode()
        subprocess.run(["hostnamectl", "set-hostname", f"{hostname}.{domain.lower()}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting hostname: {e}")
        sys.exit(1)

def join_domain(domain, domain_admin_account, domain_admin_password):
    try:
        subprocess.run(["echo", domain_admin_password], check=True)
        subprocess.run(["sudo", "realm", "join", "-v", "-U", domain_admin_account, domain], input=domain_admin_password, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error joining domain: {e}")
        sys.exit(1)

def configure_sudoers():
    try:
        with open("/etc/sudoers.d/domain_admins", "w") as sudoers_file:
            sudoers_file.write("%linux_admins ALL=(ALL) ALL\n")
    except IOError as e:
        print(f"Error writing to /etc/sudoers.d/domain_admins: {e}")
        sys.exit(1)

def update_sssd_conf(domain):
    try:
        with open("/etc/sssd/sssd.conf", "a") as sssd_conf:
            sssd_conf.write("\nfull_name_format = %1$s\n")
            sssd_conf.write(f"default_domain_suffix = {domain.upper()}\n")
        subprocess.run(["sed", "-i", "s/%u@%d/%u/", "/etc/sssd/sssd.conf"], check=True)
    except IOError as e:
        print(f"Error updating /etc/sssd/sssd.conf: {e}")
        sys.exit(1)

def enable_pam_mkhomedir():
    try:
        subprocess.run(["pam-auth-update", "--enable", "mkhomedir"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error enabling pam_mkhomedir: {e}")
        sys.exit(1)

def main():
    if os.geteuid() != 0:
        print("Please run as superuser (root) to use this script!")
        sys.exit(1)

    domain = input("Enter the domain: ")
    domain_admin_account = input("Enter the domain admin account: ")
    domain_admin_password = getpass.getpass("Enter the domain admin password: ")

    install_packages()
    configure_kerberos(domain)
    join_domain(domain, domain_admin_account, domain_admin_password)
    configure_sudoers()
    update_sssd_conf(domain)
    enable_pam_mkhomedir()

if __name__ == "__main__":
    main()

