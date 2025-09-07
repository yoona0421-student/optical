# Publish interactive map with GitHub Pages

Quick steps to publish the interactive `tashu_presentation_map.html` using GitHub Pages (project site). These commands assume you have git configured and a GitHub repository created for this project.

Windows (cmd) quick sequence:

1) Initialize repo (if needed):

```
git init
git add .
git commit -m "Initial commit: add presentation map"
git branch -M main
git remote add origin <your-git-remote-url>
git push -u origin main
```

2) Enable GitHub Pages: go to your repository Settings → Pages → Source and select the `main` branch (root) or enable GitHub Actions deployment.

3) (Optional) Use GitHub Actions to publish to `gh-pages` branch automatically. See `.github/workflows/gh-pages.yml` in this repo for a sample workflow.

After publishing, your map will be available at `https://<your-username>.github.io/<repo-name>/`.
