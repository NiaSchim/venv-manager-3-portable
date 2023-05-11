import os
import sys
import subprocess
import urllib.request
import json
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
import venv
import shutil


class VirtualEnvManager:
    def __init__(self):
        pass

    def create_venv(self, path, interpreter=None, system_site_packages=False, symlinks=False, copies=False):
        parent_venv = self.find_parent_venv(path)
        if parent_venv:
            inherit_dependencies = messagebox.askyesno(
                "Inherit dependencies",
                "A parent virtual environment has been detected. Do you want the new virtual environment to inherit its dependencies?",
            )
            if inherit_dependencies:
                system_site_packages = True

            python_version = sys.version_info
            parent_python_version = self.get_python_version(parent_venv)
            if python_version != parent_python_version:
                proceed = messagebox.askyesno(
                    "Python versions mismatch",
                    f"The parent virtual environment uses Python {parent_python_version.major}.{parent_python_version.minor}, while the current Python interpreter uses version {python_version.major}.{python_version.minor}. They may not perfectly match each other's capacities. Do you still want to proceed?",
                )
                if not proceed:
                    return

        builder = venv.EnvBuilder(system_site_packages=system_site_packages, symlinks=symlinks, clear=True)
        builder.create(path)

        if interpreter:
            self.install_python_interpreter(path, interpreter)

        if copies:
            activate_script_path = os.path.join(path, "bin", "activate")
            with open(activate_script_path, "r") as file:
                content = file.readlines()

            content[43] = 'VIRTUAL_ENV="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}" )")" && pwd)"\n'

            with open(activate_script_path, "w") as file:
                file.writelines(content)

            pip_scripts = [os.path.join(path, "bin", "pip"), os.path.join(path, "bin", "pip3")]
            for script in pip_scripts:
                with open(script, "r") as file:
                    content = file.readlines()

                content[0] = "#!/usr/bin/env python\n"

                with open(script, "w") as file:
                    file.writelines(content)

    def find_parent_venv(self, path):
        while path != os.path.dirname(path):
            path = os.path.dirname(path)
            if self.is_venv(path):
                return path
        return None

    def get_python_version(self, venv_path):
        if sys.platform == "win32":
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")
        result = subprocess.run([python_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        version_string = result.stdout.strip() if result.stdout else result.stderr.strip()
        try:
            return tuple(map(int, version_string.split()[1].split(".")))
        except ValueError:
            messagebox.showerror("Error", "Unable to determine the Python version.")
            return None


    def clone_current_interpreter(self, venv_path):
        current_interpreter = sys.executable
        builder = venv.EnvBuilder(clear=True, with_pip=True)
        builder.create(venv_path)

        activate_script_path = os.path.join(venv_path, "bin", "activate")
        with open(activate_script_path, "r") as file:
            content = file.readlines()

        content[43] = 'VIRTUAL_ENV="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}" )")" && pwd)"\n'

        with open(activate_script_path, "w") as file:
            file.writelines(content)

        pip_scripts = [os.path.join(venv_path, "bin", "pip"), os.path.join(venv_path, "bin", "pip3")]
        for script in pip_scripts:
            with open(script, "r") as file:
                content = file.readlines()

            content[0] = "#!/usr/bin/env python\n"

            with open(script, "w") as file:
                file.writelines(content)

    def prompt_interpreter_path(self):
        use_current_interpreter = messagebox.askyesno(
            "Use current interpreter",
            "Do you want to use the current Python interpreter?",
        )
        if use_current_interpreter:
            return sys.executable
        else:
            while True:
                path = filedialog.askopenfilename(
                    title="Select Python interpreter",
                    filetypes=[("Python interpreter", "*.exe"), ("Python interpreter", "python")],
                )
                if not path:
                    if messagebox.askyesno(
                        "Use current interpreter",
                        "Do you want to use the current Python interpreter?",
                    ):
                        return sys.executable
                    else:
                        continue
                elif os.path.isfile(path) and path.endswith(("python.exe", "python")):
                    return path
                else:
                    messagebox.showerror(
                        "Invalid interpreter path", "Please select a valid Python interpreter."
                    )

    def install_python_interpreter(self, venv_path, interpreter):
        dest_path = os.path.join(venv_path, "bin", "python")
        shutil.copy2(interpreter, dest_path)

    def install_package(self, venv_path, package_name):
        pip_path = os.path.join(venv_path, "bin", "pip")
        subprocess.run([pip_path, "install", package_name])

    def is_venv(self, path):
        if os.name == 'nt':  # Windows
            scripts_path = os.path.join(path, "Scripts")
            pyvenv_cfg_path = os.path.join(path, "pyvenv.cfg")
            include_path = os.path.join(path, "Include")
            lib_path = os.path.join(path, "Lib")

            return (
                os.path.exists(scripts_path)
                and os.path.exists(pyvenv_cfg_path)
                and os.path.exists(include_path)
                and os.path.exists(lib_path)
            )
        else:  # Unix systems
            bin_path = os.path.join(path, "bin")
            if not os.path.exists(bin_path):
                return False

            python_path = os.path.join(bin_path, "python")
            if not os.path.exists(python_path):
                return False

            return True

    def run_script(self, venv_path, script_path):
        if not self.is_venv(venv_path):
            raise ValueError("Not a valid virtual environment path")

        python_path = os.path.join(venv_path, "bin", "python")
        subprocess.run([python_path, script_path])

class VirtualEnvManagerGUI:
    def __init__(self, manager):
        self.manager = manager
        self.root = tk.Tk()

    def create_main_window(self):
        self.root.title("VirtualEnv Manager")

        create_venv_button = tk.Button(self.root, text="Create Virtual Environment", command=self.on_create_venv_button_click)
        create_venv_button.pack()

        install_python_interpreter_button = tk.Button(self.root, text="Install Python Interpreter", command=self.on_install_python_interpreter_button_click)
        install_python_interpreter_button.pack()

        install_package_button = tk.Button(self.root, text="Install Package", command=self.on_install_package_button_click)
        install_package_button.pack()

        run_script_button = tk.Button(self.root, text="Run Script", command=self.on_run_script_button_click)
        run_script_button.pack()

        self.root.mainloop()

    def on_create_venv_button_click(self):
        path = self.select_directory()
        interpreter = self.manager.prompt_interpreter_path()  # Use the method from the manager class
        self.manager.create_venv(path, interpreter=interpreter, copies=True)
        messagebox.showinfo("Success", "Virtual environment created successfully.")

    def on_install_python_interpreter_button_click(self):
        venv_path = self.select_directory()
        interpreter_path = self.prompt_interpreter_path()
        self.manager.install_python_interpreter(venv_path, interpreter_path)
        messagebox.showinfo("Success", "Python interpreter installed successfully.")

    def on_install_package_button_click(self):
        venv_path = self.select_directory()
        package_name = self.prompt_package_name()
        self.manager.install_package(venv_path, package_name)
        messagebox.showinfo("Success", f"Package '{package_name}' installed successfully.")

    def on_run_script_button_click(self):
        venv_path = self.select_directory()
        script_path = self.prompt_script_path()
        self.manager.run_script(venv_path, script_path)
        messagebox.showinfo("Success", "Script executed successfully.")

    def select_directory(self):
        return filedialog.askdirectory(title="Select a directory")

    def prompt_interpreter_path(self):
        return filedialog.askopenfilename(title="Select Python interpreter", filetypes=[("Python interpreter", "*.exe")])

    def prompt_package_name(self):
        return simpledialog.askstring("Enter package name", "Package name:")

    def prompt_script_path(self):
        return filedialog.askopenfilename(title="Select script", filetypes=[("Python scripts", "*.py")])

    def show_error(self, message):
        messagebox.showerror("Error", message)

if __name__ == "__main__":
    manager = VirtualEnvManager()
    gui = VirtualEnvManagerGUI(manager)
    gui.create_main_window()
