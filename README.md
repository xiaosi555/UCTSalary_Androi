# UCTSalary Android

Android APK build source archive: `UCTSalary_Android.zip`

## Build

GitHub Actions automatically builds a debug APK when the source archive or build workflow changes on `main`.

- Workflow: [Build UCTSalary Android APK](../../actions/workflows/android-apk.yml)
- Artifact: `UCTSalary-Android-debug-APK`
- Build task: `assembleDebug`
- Artifact retention: 14 days

Download the APK from the completed workflow run's **Artifacts** section.

Build workflow uses explicit Android SDK packages to avoid obsolete SDK tools.

CI build configuration refreshed.
