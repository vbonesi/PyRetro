plugins { id("com.android.application"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.plugin.compose") }
android {
    namespace = "com.pyretro.app"
    compileSdk = 35
    defaultConfig { applicationId = "com.pyretro.app"; minSdk = 26; targetSdk = 35; versionCode = 49; versionName = "0.28.0" }
    defaultConfig { testInstrumentationRunner = "com.pyretro.app.StorageSmoke" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
    signingConfigs.getByName("debug") { storeFile = rootProject.file(".gradle/debug.keystore") }
}
dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.05.01"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.work:work-runtime:2.10.5")
    implementation("com.google.android.gms:play-services-auth:21.2.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}
