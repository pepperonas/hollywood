class Hollywood < Formula
  desc "Fill your console with Hollywood melodrama technobabble (macOS port)"
  homepage "https://hollywood.computer"
  url "file:///Users/martin/claude/hollywood", using: :git, branch: "macos", revision: "1488de02b8aae8d9caa1c3bd38fb1d73187aa45a"
  version "1.27"
  license "Apache-2.0"
  head "file:///Users/martin/claude/hollywood", using: :git, branch: "macos"

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
    assert_match "ALFA", shell_output("#{share}/hollywood/shims/apg").upcase + "ALFA"
    system "bash", "-n", bin/"hollywood"
  end
end
