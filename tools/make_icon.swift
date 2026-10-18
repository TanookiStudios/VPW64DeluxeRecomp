// make_icon.swift - draws the app icon: original pixel art (a wrestler with arms raised
// in a ring under the arena lights), nothing taken from the game.
//
//   swift tools/make_icon.swift <out.png> <size> [--full]
//
// Default: macOS icon layout (artwork inset in a rounded square, transparent
// margin). --full: artwork fills the square (Windows .ico, launcher, README).
import AppKit

let args = CommandLine.arguments
let outPath = args[1]
let size = Int(args[2])!
let full = args.contains("--full")

func rgb(_ hex: UInt32) -> NSColor {
    NSColor(srgbRed: CGFloat((hex >> 16) & 255) / 255, green: CGFloat((hex >> 8) & 255) / 255,
            blue: CGFloat(hex & 255) / 255, alpha: 1)
}

// 32 x 32 grid, row 0 at the top.
var grid = [[UInt32?]](repeating: [UInt32?](repeating: nil, count: 32), count: 32)
func fillRows(_ a: Int, _ b: Int, _ color: UInt32) { for r in a...b { for c in 0..<32 { grid[r][c] = color } } }
func put(_ c: Int, _ r: Int, _ color: UInt32) { if (0..<32).contains(c) && (0..<32).contains(r) { grid[r][c] = color } }
func box(_ c0: Int, _ r0: Int, _ c1: Int, _ r1: Int, _ color: UInt32) { for r in r0...r1 { for c in c0...c1 { put(c, r, color) } } }

// Arena: near-black top, a soft spotlight glow behind the wrestler, and a crowd band.
fillRows(0, 13, 0x0B0D1E)
for r in 0...13 { for c in 0..<32 {
    let dx = Double(c) + 0.5 - 16, dy = (Double(r) + 0.5 - 2) * 1.6
    let d = dx * dx + dy * dy
    if d < 36 { grid[r][c] = 0x2A2F5C } else if d < 90 { grid[r][c] = 0x1A1E3E } else if d < 150 { grid[r][c] = 0x12152C }
} }
// Rig lights along the top.
for c in stride(from: 2, through: 29, by: 9) { put(c, 1, 0xFFF1A8); put(c + 1, 1, 0xFFF1A8); put(c, 2, 0xFFD24A); put(c + 1, 2, 0xFFD24A) }
// Crowd: speckled heads in muted colors.
let crowd: [UInt32] = [0x5A4634, 0x7A6248, 0x3E4A6A, 0x6A3E3E, 0x4C5A3E, 0x8A7A6A]
for r in 9...13 { for c in 0..<32 where (c * 7 + r * 11) % 5 != 0 { grid[r][c] = crowd[(c * 3 + r * 5) % crowd.count] } }

// Ring: blue mat with the apron below, red ropes on three rows, red and blue posts.
box(0, 14, 31, 25, 0x2F7FD8)                      // mat
box(0, 22, 31, 25, 0x2669B8)                      // mat, nearer edge a touch darker
box(0, 26, 31, 31, 0xB8202A)                      // apron
for c in 0..<32 where c % 4 == 1 { box(c, 27, c, 30, 0xE8E8E8) }   // apron skirt stripes
for r in [15, 18, 21] { fillRows(r, r, 0xD82A34); for c in 0..<32 where c % 6 == 3 { put(c, r, 0xF0F0F0) } }  // ropes with tie-offs
box(2, 11, 3, 26, 0xC8202C); box(2, 11, 3, 12, 0xFF6A6A)      // left post, red
box(28, 11, 29, 26, 0x2050C8); box(28, 11, 29, 12, 0x6A8CFF)  // right post, blue
box(1, 26, 4, 26, 0xE8E8E8); box(27, 26, 30, 26, 0xE8E8E8)    // turnbuckle pads at the floor

// The wrestler: arms up, facing the crowd. Original figure, no game sprite.
let skin: UInt32 = 0xE8B88A, skinDark: UInt32 = 0xC08A5C, hair: UInt32 = 0x2A1810
let singlet: UInt32 = 0x1E8A48, singletLight: UInt32 = 0x3CB464, tights: UInt32 = 0xF4F4F4, tightsShade: UInt32 = 0xC8CCD4
let boot: UInt32 = 0x1A1A24, ink: UInt32 = 0x0A0A14
// Head and hair.
box(14, 7, 17, 11, skin); box(14, 7, 17, 8, hair); put(14, 9, hair); put(17, 9, hair)
put(15, 10, skinDark); put(16, 10, skinDark)      // brow shadow
// Neck and shoulders.
box(15, 12, 16, 12, skinDark)
box(12, 13, 19, 13, skin)
// Arms raised: upper arms out, forearms up, fists.
box(10, 12, 11, 13, skin); box(20, 12, 21, 13, skin)
box(9, 8, 10, 11, skin); box(21, 8, 22, 11, skin)
box(9, 6, 10, 7, skinDark); box(21, 6, 22, 7, skinDark)   // fists
// Torso in the singlet, with a lighter stripe.
box(12, 14, 19, 19, singlet); box(13, 14, 13, 19, singletLight); box(18, 14, 18, 19, singletLight)
box(12, 14, 19, 14, skin)                         // chest above the singlet line
// Legs in white tights, boots.
box(12, 20, 14, 24, tights); box(17, 20, 19, 24, tights)
box(12, 20, 12, 24, tightsShade); box(17, 20, 17, 24, tightsShade)
box(12, 25, 14, 26, boot); box(17, 25, 19, 26, boot)
// Outline: any figure cell next to a non-figure cell gets an ink edge on its outside.
let figure: Set<UInt32> = [skin, skinDark, hair, singlet, singletLight, tights, tightsShade, boot]
var outline = [(Int, Int)]()
for r in 5...27 { for c in 7...24 {
    guard let v = grid[r][c], figure.contains(v) else { continue }
    for (dc, dr) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
        let nc = c + dc, nr = r + dr
        if let n = grid[nr][nc], figure.contains(n) { continue }
        outline.append((nc, nr))
    }
} }
for (c, r) in outline { put(c, r, ink) }

// Render: whole pixels only, so the art stays crisp.
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size, bitsPerSample: 8,
                           samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
                           bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
let ctx = NSGraphicsContext(bitmapImageRep: rep)!
NSGraphicsContext.current = ctx
ctx.imageInterpolation = .none
ctx.shouldAntialias = false

let art = full ? CGFloat(size) : CGFloat(size) * 832 / 1024   // Apple's grid: 824-ish content in 1024
let cell = art / 32
let origin = (CGFloat(size) - art) / 2
let radius = art * (full ? 0.18 : 0.225)
let frame = NSRect(x: origin, y: origin, width: art, height: art)
ctx.shouldAntialias = true
NSBezierPath(roundedRect: frame, xRadius: radius, yRadius: radius).addClip()
ctx.shouldAntialias = false
for r in 0..<32 {
    for c in 0..<32 {
        guard let color = grid[r][c] else { continue }
        rgb(color).setFill()
        // AppKit's y axis points up; row 0 is the top.
        let x = (origin + CGFloat(c) * cell).rounded(.down)
        let y = (origin + art - CGFloat(r + 1) * cell).rounded(.down)
        let x2 = (origin + CGFloat(c + 1) * cell).rounded(.down)
        let y2 = (origin + art - CGFloat(r) * cell).rounded(.down)
        NSRect(x: x, y: y, width: x2 - x, height: y2 - y).fill()
    }
}
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: outPath))
