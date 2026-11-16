# Security review — 1.0.2

Local review of the source at https://github.com/KIexster/DestinyRising-FoundryTracker.

## Changes
- Pin SHA-256 identities of bundled adb.exe and both ADB DLLs in source. Validate the bundle before setup and the private copy before returning it. Shutdown validates the executable and DLLs too. A stale copy is stopped using the verified bundled executable, never the stale executable.
- Remove inherited ADB socket/address overrides before selecting the private server port.
- Validate argument types, control characters and device selectors before ADB execution. Preserve the existing read-only command allowlist.
- Reject transfers outside 1 byte–16 MiB before opening a root shell; limit individual response lines and preserve exact byte-count checks and timeouts.
- Bound local JSON loads to 8 MiB and handle malformed/deep JSON with defaults. Use unique temporary files for atomic settings/history writes.
- Run security regression tests as part of build. Validate the release version and containment of the release staging directory before recursive cleanup.

## Validation
45 existing tests and 7 security tests passed. Tests cover altered ADB executables/DLLs, shutdown of an untrusted binary, invalid selectors/arguments, oversized transfers, malformed JSON and temporary-file collisions. Release uses the existing --noupx build. The compiled live diagnostic did not finish within 55 seconds, so live gameplay-counter reading was not revalidated in this session.

## Limits and release recommendations
This is a targeted source review, not a certification, exhaustive audit or guarantee against all attacks. Hash pins protect the ADB cache from replacement relative to this application; an attacker able to replace the whole application can replace its checks. There remains a possible local check/use race; Windows ACLs and trusted distribution matter. The app still requires root access in the emulator to read the game's memory. Root does not extend to Windows administrator rights.

The examined runtime source has no HTTP updater or telemetry uploader. No updater signatures or transport security were claimed or added. engine.json remains a local data override, not executable code or a remotely authenticated update channel.

The executable is not Authenticode signed. A legitimate publisher certificate and timestamped release signing are recommended for public releases; no certificate was available in this review. A checksum alone does not authenticate the publisher. Publish release checksums through your trusted GitHub release channel and retain source for review. Do not promise that antivirus/SmartScreen will never flag memory-reading software. Do not disable antivirus or add exclusions as a workaround.

No files were pushed or published by this review. No public malware-scanning service was given the executable or private account data.
