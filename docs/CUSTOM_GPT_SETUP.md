# Set up a private Custom GPT Action

This guide assumes the API has been deployed to a private HTTPS URL. Localhost cannot be called by ChatGPT.

1. Generate a random API key containing at least 32 characters. Store it in the hosting provider’s secret settings as `DESIGN_FLOW_API_KEY`.
2. Mount persistent storage and set `DESIGN_FLOW_PROJECT_ROOT` to that mount.
3. Deploy the included container and verify `https://YOUR-HOST/docs` opens.
4. Run `python -m design_flow_action_api --export-openapi openapi.json` with the same public server configuration, or use the committed `openapi.json` after replacing its server URL when required by the GPT builder.
5. Open ChatGPT’s GPT builder and create or edit a private GPT.
6. Open Actions and import `openapi.json`.
7. Configure API-key authentication. Use custom header `X-API-Key` and paste the same secret stored by the host.
8. Paste [Custom GPT instructions](CUSTOM_GPT_INSTRUCTIONS.md) into the GPT Instructions field.
9. Test `listProjects`, then create or resume a project.
10. Import and preview a draft. Confirm the GPT does not lock automatically.
11. Explicitly approve the reviewed draft and confirm `lockRound` asks permission before execution.

## Acceptance conversation

```text
User: Open my Design Flow project "Example Project".
GPT: listProjects -> resumeProject -> reports current brief
User: Show unresolved questions.
GPT: getUnresolved
User: Import this round as a draft.
GPT: importDraft -> previewDraft -> explains effects -> DOES NOT LOCK
User: Yes, commit it.
GPT: lockRound -> compileContextHandoff -> reports success
```

This is private single-user API-key authentication. It is not OAuth, tenancy, sharing, or a public app submission architecture.

Never save the key in a project file, committed `.env` file, container image, or Docker build context. Supply it through the hosting provider's secret management or the process environment.
