# LaunchPack

**Product in. Launch posts out. For 112 platforms.**

Give LaunchPack your product (a GitHub repo, a project folder, a README,
or even one plain paragraph) and it writes a launch post for every
platform you pick, each one in BOTH Markdown (.md) and plain text (.txt).
No API key. No AI model. No account. It runs fully offline with pure
rules, and it writes only from facts you gave it. It never invents
features, numbers or results. Story gaps stay as clear [bracketed
placeholders], because your story is yours.

## Run it

**Windows:** double-click `LaunchPack.bat`. The pro web UI opens.
**macOS / Linux:** `./launchpack.sh`. The pro web UI opens.
**Terminal fans:** pass arguments to either launcher, or run
`python3 launchpack.py ...` directly. Examples below.

Needs only Python 3.10+. The UI is a local web page served by Python
itself (127.0.0.1 only): it opens in a desktop window when pywebview is
installed, otherwise in your default browser. A Tkinter fallback
(`launchpack_gui.py`) is included too.

## The GUI

A dark, professional three-panel window: Source on the left, the
searchable platform list in the middle, Output on the right with the
format switch and one big GENERATE POSTS button. Live selected count
in the footer. Screenshot: `docs/gui.png`.

1. Pick your source: GitHub URL, local folder, a README file, or one paragraph.
   The Strict No-AI toggle keeps story gaps as [brackets]; off fills them with neutral lines.
2. Tick platforms. Presets: Launch day, Social, Dev, All, None.
   112 platforms in four groups: launch boards and directories,
   communities and blogs, social platforms, formats and stores
   (including Google Play, App Store and Steam page copy).
3. Tick formats (.md, .txt, or both), hit GENERATE POSTS.

Every platform's real limits are respected. An X post is trimmed to
280 characters, a Product Hunt tagline fits its box, a Show HN post
reads like a Show HN post.

## Terminal examples

```bash
python3 launchpack.py https://github.com/you/your-repo --preset all
python3 launchpack.py --folder ~/projects/myapp --preset launch
python3 launchpack.py --text "MyApp is a free tool that ..." --preset social
python3 launchpack.py --name "MyApp" --tagline "Does X for Y" --features "Fast; Offline; Free" --platforms x,linkedin,producthunt
python3 launchpack.py --list-platforms
```

## How the paragraph mode works

Paste one honest paragraph about your product. LaunchPack splits it
into sentences, finds the product name ("X is ..."), makes the first
sentence your tagline, and picks feature sentences by cue words
(can, lets, helps, includes, supports, automatically). No model, no
key, nothing leaves your machine.

## Output

One folder with one file per platform per format, plus `index.txt`:
`producthunt.md`, `producthunt.txt`, `x.md`, `x.txt`, and so on.

## See it work

`examples/` holds real output generated from real products, unedited.

## Tested

The generator is validated end to end: 4 input modes x 112 platforms x
2 formats = 896 files checked for presence, sane length, platform
character limits and clean punctuation. The GUI is smoke-tested the
same way, and both launchers (bat and sh) are run before every release.

## Honest limits

- It drafts, you finish. The [bracketed] lines (your problem story, the
  one thing you want feedback on) are where launches are won.
- A thin README makes thin posts. That is worth knowing before launch day.

## License

MIT. Built by [Tanmoy Majumder](https://github.com/Tcode-Motion)
(@tcodemotion), during launch season, for makers who ship.
