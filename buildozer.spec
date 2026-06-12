[app]
title = StudyMate
package.name = studymate
package.domain = org.studymate
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,db
version = 1.0.0
requirements = python3,kivy==2.2.1,plyer,android
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.2.1
fullscreen = 0
presplash.color = #1A1A2E
icon = icon.png
android.gradle_dependencies = 'com.google.android.gms:play-services-base:18.2.0'
android.enable_services = 
android.api = 34
android.minapi = 21
android.ndk = 25c
android.gradle_source_task = 
android.archs = arm64-v8a
android.accept_sdk_license = True
android.compile_sdk = 34
android.manifest_intent_filters =

[buildozer]
log_level = 2
warn_on_root = 1
debug = 1
