[app]
# (str) Title of your application
title = Overdrive
# (str) Package name
package.name = overdrive
# (str) Package domain (needed for android/ios packaging)
package.domain = org.test
# (str) Source code where the main.py live
source.dir = .
# (str) Source code filename (let empty to use all the files)
source.include_exts = py,png,jpg,kv,atlas
# (str) Application versioning (method 1)
version = 1.0
# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.2.1,plyer,pyjnius,android

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png
# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,VIBRATE,WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 33
# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching, for example:
# OUYA-ODK/libs/*.jar
# android.add_jars = foo.jar,bar.jar,path/to/more/*.jar

# (str) Bootstrap to use for android builds
p4a.branch = master

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2
# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
