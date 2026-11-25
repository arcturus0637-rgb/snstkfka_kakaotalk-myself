# snstkfka_kakaotalk-myself

A Codex skill for **sending explicitly requested text and file links to your own KakaoTalk self chat** through a separately configured MCP server. It confirms successful delivery, preserves retry identifiers and avoids unsolicited messages.

**This repository contains the skill and an MCP client helper. It does not include a Kakao OAuth application, a standalone MCP server, a file-hosting service, credentials or access to the author's private server.** You must provide your own compatible backend before sending anything.

## Features

- Send a selected message or file only when the user explicitly requests it.
- Use a fresh `request_id` for each new request and reuse it only for retries of that same request.
- Confirm `status: "sent"` and `kakao_result_code: 0` before reporting delivery.
- Verify the uploaded file's SHA-256 against the local file through the configured MCP implementation.
- Report uncertain delivery instead of automatically resending with a new identifier.
- Use a read-only connection status check without sending a test message.

File delivery means an **HTTPS download link**, not a native KakaoTalk file attachment. Anyone holding the link may access it until expiry. The backend must host the file and implement the retention policy it advertises.

The workflow instructions are written in Korean. Repository documentation and metadata summaries are in English.

## Requirements

1. Your own Kakao developer application and authorized KakaoTalk self-message connection. Follow [Kakao's official message API documentation](https://developers.kakao.com/docs/latest/ko/kakaotalk-message/rest-api).
2. A compatible MCP server registered in Codex as `news-briefing`, implementing the contract below.
3. For file delivery, your own HTTPS file hosting, unguessable download links, expiry cleanup and content-integrity checks.
4. Only for the optional fallback helper: Python 3.11+ and the dependencies in [requirements.txt](requirements.txt).

Keep tokens and private connection settings outside this repository. This skill does not create a Kakao app, complete OAuth, register an MCP backend or change a news schedule for you.

## Install the skill

Use Codex's bundled installer if available. It refuses to overwrite an existing `kakao-self-send` installation.

**PowerShell**

```powershell
$codexDir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
python (Join-Path $codexDir 'skills/.system/skill-installer/scripts/install-skill-from-github.py') --repo arcturus0637-rgb/snstkfka_kakaotalk-myself --path skills/kakao-self-send
```

**macOS / Linux / WSL**

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo arcturus0637-rgb/snstkfka_kakaotalk-myself --path skills/kakao-self-send
```

Alternatively, copy `skills/kakao-self-send` into your Codex skills directory. Start a new chat after installing and configuring the MCP server.

## MCP contract

The public skill expects these tool names. The fallback helper uses the **stdio** server's `command`, `args` and optional `env` in the user's own Codex `config.toml`.

| Tool | Required behavior |
| --- | --- |
| `get_news_briefing_status()` | Return whether the self-send connection is configured and describe the actual text, file and retention limits; send nothing. |
| `kakao_send_text(text, request_id)` | Send user-requested text to the authenticated user's self chat. Persist idempotency state and return confirmed delivery status. |
| `kakao_send_file(file_path, request_id, message="", ttl_days=7, dry_run=False)` | Read the explicitly selected local file on the client side, upload its exact bytes to the user's file host and send its link. `dry_run=True` uploads/prepares without sending a Kakao message. Return the file hash and actual expiry policy. |
| `get_latest_news_briefing()` | Optional for self-send; when provided, read the latest saved briefing without collecting new data or sending a message. Its content is untrusted data, not instructions. |

The reference contract uses a 1,200 UTF-16-unit text limit, a 25 MiB file limit, a default seven-day retention period and an optional `ttl_days` range of 1–30. Those limits belong to the backend contract; check the actual server's status before describing them to the user. They are not asserted as Kakao API-wide limits.

A successful text result contains:

```json
{
  "status": "sent",
  "kakao_result_code": 0
}
```

A successful file result additionally includes a `file` object with `sha256`, `url` and expiry information. The MCP implementation must verify the hash against the local bytes before reporting success. An uncertain timeout must not be reported as a success or retried automatically with a new `request_id`.

Installing an unrelated news MCP with the same name is insufficient; its tool schemas and delivery behavior must match this contract. A backend that only renders text or returns a URL without delivering it must not claim `status: "sent"`.

## Use in Codex

Once your backend is connected:

```text
$kakao-self-send Send “The report is ready” to my own KakaoTalk.
```

```text
$kakao-self-send Send this PDF to my KakaoTalk as a download link.
```

The skill may also be selected for a clear natural-language send request. Ordinary answers, news summaries and files are never sent automatically merely because this skill is installed.

## Optional fallback client

If a chat cannot see the configured MCP tools yet, the helper can call that same server through the MCP SDK. It does not bypass authentication or provide a replacement backend.

From a clone of this repository:

```bash
python -m pip install -r requirements.txt
python -X utf8 skills/kakao-self-send/scripts/call.py --list-tools
python -X utf8 skills/kakao-self-send/scripts/call.py get_news_briefing_status
```

For a user-authorized send, pass the tool arguments in a UTF-8 JSON file:

```bash
python -X utf8 skills/kakao-self-send/scripts/call.py kakao_send_file --arguments-file /absolute/path/to/send-arguments.json
```

The helper honors `CODEX_HOME`; otherwise it reads `~/.codex/config.toml`. A disabled, absent or non-stdio server is rejected. Keep argument files out of version control when they contain private messages, filenames or links.

## Scope and verification

This is a client skill for self-send only. It does not expose tools for friends, groups, channels, brokerage accounts or trading. The release was checked for valid skill metadata, portable paths, accidental private-data inclusion and fallback-client operation against a local mock MCP. No real Kakao message was sent to publish or validate this package.

## License

[MIT](LICENSE) for this repository's custom skill and client helper. Kakao, Codex, Python dependencies and your MCP backend have their own terms and licenses. Independent community project; not an official Kakao, OpenAI or Anthropic product.
