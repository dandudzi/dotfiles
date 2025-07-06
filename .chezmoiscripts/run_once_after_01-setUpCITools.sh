echo "📲 installing xcode-select tools"
xcode-select --install

echo "⏳rebuilt bat cache"
bat cache --build

echo "📊 setup sketchybar"
curl -L https://github.com/kvndrsslr/sketchybar-app-font/releases/download/v2.0.28/sketchybar-app-font.ttf -o $HOME/Library/Fonts/sketchybar-app-font.ttf
(git clone https://github.com/FelixKratz/SbarLua.git /tmp/SbarLua && cd /tmp/SbarLua/ && make install && rm -rf /tmp/SbarLua/)

sketchybar --load-font "Symbols Nerd Font"
sketchybar --load-font "Symbols Nerd Font Mono"
sketchybar --load-font "CommitMono"

brew services restart sketchybar
echo "🐁 mise installation of tools"
mise install
