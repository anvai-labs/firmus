# GitHub Release Checklist

## Pre-Release Tasks

- [x] Rename project to FIRMUS (Firewall-traversing Independent Remote Monitoring and Uninterrupted Filesystem Access System)
- [x] Professional class renaming (DataCollector, MonitoringAgent)
- [x] Remove sensitive data (p2pt directory with adi/pyspark files)
- [x] Create LICENSE file (MIT)
- [x] Create SECURITY.md with limitations
- [x] Create DISCLAIMER.md for authorized use
- [x] Create comprehensive README.md
- [x] Create Medium blog post
- [x] Initialize git repository
- [x] Create initial commit

## GitHub Setup Tasks

- [ ] Create GitHub repository named `firmus`
- [ ] Add repository description: "Research implementation for firewall-traversing remote filesystem monitoring of IoT devices behind NAT/firewalls"
- [ ] Add tags: `iot`, `remote-monitoring`, `firewall`, `nat-traversal`, `research`, `python`, `udp`
- [ ] Set license to MIT
- [ ] Push local repository to GitHub

## Commands to Push to GitHub

```bash
cd /Users/vijaysingh/code/firmus

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/firmus.git

# Push to GitHub
git push -u origin main
```

## Post-Release Tasks

- [ ] Verify repository on GitHub
- [ ] Create GitHub Release (v1.0.0)
- [ ] Add release notes with security warnings
- [ ] Enable GitHub Issues for bug reports
- [ ] Enable GitHub Discussions for questions
- [ ] Add CODE_OF_CONDUCT.md if accepting contributions
- [ ] Add CONTRIBUTING.md for contribution guidelines
- [ ] Consider adding GitHub Actions for CI/testing
- [ ] Add Zenodo DOI for citation (optional)

## Release Notes Template

```markdown
# FIRMUS v1.0.0

## Research Release

This is the first public release of FIRMUS, a research implementation for
remote filesystem monitoring of IoT and edge devices behind NAT/firewalls.

## ⚠️ Important Security Notice

This is a research prototype, NOT production-ready software:
- No encryption (cleartext UDP communication)
- No authentication (anyone can connect)
- No authorization (no access control)

See [SECURITY.md](SECURITY.md) for details.

## Features

- Data Collector (server) and Monitoring Agent (client)
- Firewall/NAT traversal via outbound connections
- No root privileges required (user-space UDP)
- Remote directory listing (flat and recursive)
- File download with progress tracking
- Lightweight (~600 lines, Python stdlib only)

## Use Cases

- IoT device monitoring
- Remote data collection
- Home server administration
- Authorized incident response

## Documentation

- [README.md](README.md) - Getting started
- [SECURITY.md](SECURITY.md) - Security limitations
- [DISCLAIMER.md](DISCLAIMER.md) - Legal and ethical use
- [MEDIUM_BLOG_POST.md](MEDIUM_BLOG_POST.md) - Detailed explanation

## Requirements

- Python 3.8+
- Network connectivity between collector and agents

## Quick Start

```bash
# Collector (server)
python3 remote_filesystem_research.py collector udp --port 5353

# Agent (client)
python3 remote_filesystem_research.py agent udp --collector HOST:5353 --dir /data
```

## Citation

If you use this in research, please cite:

```bibtex
@software{firmus2024,
  title = {FIRMUS: Firewall-traversing Independent Remote Monitoring System},
  year = {2024},
  url = {https://github.com/YOUR_USERNAME/firmus}
}
```

## License

MIT License - see [LICENSE](LICENSE)

## Disclaimer

For authorized use only. See [DISCLAIMER.md](DISCLAIMER.md).
```

## URLs to Update

After creating the repository, update these URLs in the files:

- [ ] README.md - GitHub URLs
- [ ] MEDIUM_BLOG_POST.md - Repository link
- [ ] CITATION in README.md - Update GitHub username

## Optional Enhancements

- [ ] Add GitHub Actions for linting/testing
- [ ] Add issue templates
- [ ] Add PR template
- [ ] Set up dependabot (if dependencies added)
- [ ] Add funding.yml for sponsor link
- [ ] Create website/GitHub Pages
- [ ] Register with Zenodo for DOI
