"""
모든 플랫폼 빌드 스크립트
GitHub Actions를 사용하여 Windows, macOS, Linux용 실행 파일을 빌드합니다.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path


def check_git():
    """Check if git is initialized and has remote."""
    try:
        # Check if git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, "Git 저장소가 아닙니다. 'git init'을 먼저 실행하세요."

        # Check if has remote
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            return False, "GitHub 원격 저장소가 설정되지 않았습니다."

        # Get remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True
        )
        remote_url = result.stdout.strip()

        return True, remote_url

    except Exception as e:
        return False, f"Git 확인 실패: {e}"


def get_github_repo_url(remote_url):
    """Extract GitHub repository URL from git remote."""
    # Convert SSH to HTTPS
    if remote_url.startswith("git@github.com:"):
        remote_url = remote_url.replace("git@github.com:", "https://github.com/")
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    return remote_url


def main():
    """Main process."""
    print("="*60)
    print("모든 플랫폼 빌드 (All Platforms Build)")
    print("GitHub Actions를 사용한 자동 빌드")
    print("="*60 + "\n")

    # Check git
    is_git, message = check_git()
    if not is_git:
        print(f"❌ {message}\n")
        print("GitHub Actions를 사용하려면:")
        print("1. Git 저장소 초기화:")
        print("   git init")
        print("2. GitHub에 저장소 생성")
        print("3. 원격 저장소 추가:")
        print("   git remote add origin https://github.com/YOUR_USERNAME/eumcrawl.git")
        print("4. 코드 푸시:")
        print("   git add . && git commit -m 'Initial commit' && git push -u origin main\n")
        sys.exit(1)

    remote_url = message
    github_url = get_github_repo_url(remote_url)
    actions_url = f"{github_url}/actions"

    print(f"✓ GitHub 저장소: {github_url}\n")

    # Check if there are uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    has_changes = bool(result.stdout.strip())

    if has_changes:
        print("📝 커밋되지 않은 변경사항이 있습니다.\n")
        print("변경사항:")
        subprocess.run(["git", "status", "--short"])
        print()

        response = input("커밋하고 푸시할까요? (y/n): ")
        if response.lower() == 'y':
            # Stage all changes
            subprocess.run(["git", "add", "."])

            # Commit
            commit_msg = input("커밋 메시지 입력 (Enter = 'Build all platforms'): ").strip()
            if not commit_msg:
                commit_msg = "Build all platforms"

            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True
            )
            print(result.stdout)

            # Push
            print("\n푸시 중...")
            result = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ 푸시 완료!\n")
            else:
                print("❌ 푸시 실패:")
                print(result.stderr)
                print("\n수동으로 푸시하세요: git push\n")
                sys.exit(1)
        else:
            print("\n커밋을 먼저 완료하세요:")
            print("  git add .")
            print("  git commit -m 'Build all platforms'")
            print("  git push\n")
            sys.exit(1)

    print("="*60)
    print("GitHub Actions 자동 빌드")
    print("="*60 + "\n")

    print("다음 단계:")
    print(f"1. GitHub Actions 페이지 열기:")
    print(f"   {actions_url}\n")
    print("2. 'Build Executables' workflow 클릭")
    print("3. 'Run workflow' 버튼 클릭")
    print("4. 빌드 완료 대기 (약 10-15분)")
    print("5. 'Artifacts' 섹션에서 다운로드:")
    print("   - crawler-windows (Windows EXE)")
    print("   - crawler-macos (macOS)")
    print("   - crawler-linux (Linux)")
    print("   - release-packages (전체 패키지)\n")

    print("="*60 + "\n")

    response = input("GitHub Actions 페이지를 브라우저로 열까요? (y/n): ")
    if response.lower() == 'y':
        print(f"\n브라우저 열기: {actions_url}")
        webbrowser.open(actions_url)
        print("\n✓ 브라우저에서 workflow를 수동으로 실행하세요.")
    else:
        print(f"\n수동으로 방문하세요: {actions_url}")

    print("\n" + "="*60)
    print("빌드 완료 후:")
    print("1. Artifacts 다운로드")
    print("2. 압축 해제")
    print("3. 사용자에게 배포")
    print("="*60)


if __name__ == "__main__":
    main()
