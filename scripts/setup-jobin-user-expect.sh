#!/usr/bin/expect -f
# Setup script for jobin user using expect to handle sudo password
# Usage: SUDO_PASSWORD='yourpassword' ./setup-jobin-user-expect.sh

set timeout 30
set public_key "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINnV3BW4DAkFfCFBVWC1wcmnhzu1oaQYskfFNSdf5qmL n8n-automation-jobin"
set sudo_password $env(SUDO_PASSWORD)

spawn bash -c "sudo adduser --disabled-password --gecos 'n8n automation user' jobin"
expect {
    "password" {
        send "$sudo_password\r"
        exp_continue
    }
    "already exists" {
        puts "User already exists, continuing..."
        exp_continue
    }
    eof
}

spawn bash -c "sudo usermod -aG docker jobin"
expect {
    "password" {
        send "$sudo_password\r"
        exp_continue
    }
    eof
}

spawn bash -c "sudo usermod -aG sudo jobin"
expect {
    "password" {
        send "$sudo_password\r"
        exp_continue
    }
    eof
}

spawn bash -c "sudo mkdir -p /home/jobin/.ssh && sudo chmod 700 /home/jobin/.ssh"
expect {
    "password" {
        send "$sudo_password\r"
        exp_continue
    }
    eof
}

spawn bash -c "echo '$public_key' | sudo tee /home/jobin/.ssh/authorized_keys"
expect {
    "password" {
        send "$sudo_password\r"
        exp_continue
    }
    eof
}

spawn bash -c "sudo chmod 600 /home/jobin/.ssh/authorized_keys && sudo chown -R jobin:jobin /home/jobin/.ssh"
expect {
    "password" {
        send "$sudo_password\r"
        exp_continue
    }
    eof
}

puts "\n✅ Setup complete! Testing connection..."
spawn bash -c "groups jobin"
expect eof

puts "\nUser 'jobin' is ready to use!"

