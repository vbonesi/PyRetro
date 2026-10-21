plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "com.pyretro.app"
    compileSdk = 35
    defaultConfig { applicationId = "com.pyretro.app"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "0.1.0" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    signingConfigs.getByName("debug") { storeFile = rootProject.file(".gradle/debug.keystore") }
}
dependencies { testImplementation("junit:junit:4.13.2") }
