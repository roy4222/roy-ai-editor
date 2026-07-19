# macOS editor tooling for Roy AI Editor

- Type: investigation
- Status: draft
- Date: 2026-07-18

## Question

Which editing tools should a dedicated Apple Silicon Mac mini use as Roy AI Editor
expands from Concert Live karaoke clips to general footage and natural-language edit
instructions?

The production goal is unattended, reproducible rendering. A desktop application's
feature count is secondary to whether it exposes a stable automation and interchange
seam.

## Current host

The audited host is an Apple Silicon M4 Mac mini with 24 GB RAM. None of DaVinci
Resolve, Kdenlive, Blender, CapCut, or LosslessCut is currently installed. FFmpeg and
FFprobe are also absent, so the existing repository cannot render or run its media
integration tests yet.

## Recommendation

Use a layered toolchain:

1. **Canonical edit-decision layer: OpenTimelineIO (OTIO).** Store clips, ranges,
   tracks, markers, and metadata in a project-owned representation instead of making
   a GUI editor's private project format the source of truth.
2. **Default renderer: FFmpeg with libass.** This matches the current deterministic
   karaoke, subtitle, audio, probing, and QA code. The Mac build must be tested for
   the filters and codecs the repository actually uses.
3. **Optional headless NLE experiment: MLT/melt.** It is the best free candidate when
   a multi-track timeline needs more conventional NLE rendering than direct FFmpeg.
   Adopt it only after a golden-fixture spike proves subtitle, transition, font,
   color, audio, and deterministic-output behavior.
4. **Optional motion-graphics renderer: Remotion.** It fits parameterized titles,
   karaoke animation, channel packages, and reusable graphics. Keep it outside the
   base dependency until a real template justifies the Node/Chromium stack.
5. **Optional specialist renderer: Blender.** Use it for 3D, compositing, or advanced
   motion graphics, not as the first-line editor.
6. **Human finishing only: DaVinci Resolve Free.** It is a strong inspection and
   finishing workstation, but unattended external automation should not be assumed.
   If Resolve automation becomes a product requirement, evaluate Studio and verify
   its bundled scripting contract with a render-queue smoke test.

Do not make CapCut or LosslessCut a core dependency. LosslessCut largely duplicates
the repository's FFmpeg trimming and remux capabilities. CapCut lacks a dependable,
documented project-interchange or desktop automation seam for this architecture; UI
automation would make the pipeline sensitive to app, account, region, and layout
changes.

## Tool comparison

| Tool | Role that fits | Automation/interchange | Decision now |
|---|---|---|---|
| OpenTimelineIO | Canonical timeline IR | Python/C++ API; native OTIO formats; adapters can be lossy | Add in a later architecture slice |
| FFmpeg + libass | Deterministic render, encode, audio, subtitles, QA | Stable CLI already used throughout the repo | Required base dependency |
| Kdenlive + MLT/melt | Free multi-track NLE and headless render candidate | Kdenlive writes MLT XML; `melt` renders from CLI | Golden-fixture spike only |
| Remotion | Parameterized motion graphics and channel templates | CLI render with JSON props and headless Chromium | Optional future renderer |
| Blender VSE | 3D and advanced compositing | Background CLI and Python API | Optional specialist backend |
| DaVinci Resolve | Manual review, grade, finishing | OTIO import/export; full automation belongs on a separately verified path | Optional human workstation |
| LosslessCut | Manual lossless cuts/remux | Basic CLI/API, not a full NLE | Do not add to core |
| CapCut Desktop | Manual social-video finishing | No reliable documented project automation/interchange seam found | Do not use as source of truth |

## Implementation sequence

1. Make the existing FFmpeg-first workflow reproducible on macOS: a Brewfile or
   bootstrap script, `ffmpeg`/`ffprobe` feature checks, Noto CJK font checks, Python
   environment setup, and real media smoke tests.
2. Define a renderer-neutral timeline domain model and evaluate OTIO as its serialized
   form. Keep approved lyrics, provenance, gates, and QA evidence in Roy's project
   model rather than burying them in an NLE project.
3. Run a small MLT/melt spike using one representative Concert Live fixture. Reject
   the tool if output is not deterministic or if subtitle and color behavior require
   fragile application-specific XML.
4. Add Remotion only for a concrete branded graphics template. Keep final media
   conformance and QA in the existing FFmpeg/FFprobe path.
5. Install a GUI editor only when Roy wants an intentional human finishing surface.
   It should consume/export project artifacts; it must not become the automation
   authority.

## Acceptance tests for any new renderer

- Runs non-interactively on Apple Silicon and exits with a meaningful status.
- Rebuilds the same fixture without manual clicks or hidden account state.
- Preserves clip ranges, frame rate, color expectations, audio layout, subtitle text,
  and fonts.
- Produces inspectable logs and a render manifest with tool versions and hashes.
- Passes real FFprobe, decode, audio, black/frozen-frame, subtitle safe-area, and pixel
  QA checks.
- Can be removed without losing the canonical timeline or provenance records.

## Primary sources

- [OpenTimelineIO repository](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
  and [adapter documentation](https://opentimelineio.readthedocs.io/en/latest/tutorials/adapters.html)
- [DaVinci Resolve product and Studio automation](https://www.blackmagicdesign.com/products/davinciresolve/studio),
  [support downloads](https://www.blackmagicdesign.com/support/family/davinci-resolve-and-fusion),
  and [Resolve OTIO guide](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_18.5_New_Features_Guide.pdf)
- [Kdenlive installation requirements](https://docs.kdenlive.org/en/getting_started/installation.html),
  [Kdenlive rendering](https://docs.kdenlive.org/en/exporting/render.html), and
  [MLT melt documentation](https://www.mltframework.org/docs/melt/)
- [Blender system requirements](https://www.blender.org/download/requirements/),
  [Sequence Editor API](https://docs.blender.org/api/current/bpy.types.SequenceEditor.html),
  and [command-line manual](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- [LosslessCut repository](https://github.com/mifi/lossless-cut),
  [CLI documentation](https://github.com/mifi/lossless-cut/blob/master/docs/cli.md), and
  [FAQ](https://github.com/mifi/lossless-cut/blob/master/docs/index.md)
- [CapCut desktop requirements](https://www.capcut.com/help/no-2k-or-4k-option-for-export),
  [subtitle import](https://www.capcut.com/help/how-to-import-subtitles), and
  [third-party project export limitations](https://www.capcut.com/help/how-to-export-pro-project)
- [Remotion documentation](https://www.remotion.dev/docs/),
  [render CLI](https://www.remotion.dev/docs/cli/render),
  [hardware acceleration](https://www.remotion.dev/docs/hardware-acceleration), and
  [license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)
