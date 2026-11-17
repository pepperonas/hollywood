# Homebrew formula.  The copy that brew installs lives in the tap
# (github.com/pepperonas/homebrew-tap); tools/tap-formula.sh writes it from
# this file and the checksum of the release.
class Hollywood < Formula
  desc "Fill your console with Hollywood melodrama technobabble"
  homepage "https://hollywood.celox.io"
  url "https://github.com/pepperonas/hollywood/releases/download/v1.2.0/hollywood.tar.gz"
  version "1.2.0"
  sha256 "SHA256_OF_THE_RELEASE_ARCHIVE"
  license "Apache-2.0"

  depends_on "bat"
  depends_on "bmon"
  depends_on "cmatrix"
  depends_on "figlet"
  depends_on "htop"
  depends_on "jp2a"
  depends_on "moreutils"
  depends_on "mplayer"
  depends_on "pv"
  depends_on "pygments"
  depends_on "tmux"
  depends_on "tree"

  def install
    bin.install "bin/hollywood"
    (lib/"hollywood").install Dir["lib/hollywood/*"]
    (share/"hollywood").install Dir["share/hollywood/*"]
    man1.install "share/man/man1/hollywood.1"
  end

  test do
    assert_match "hollywood #{version}", shell_output("#{bin}/hollywood --version")
    assert_match(/^\w+ \(/, shell_output("#{share}/hollywood/shims/apg"))
  end
end
