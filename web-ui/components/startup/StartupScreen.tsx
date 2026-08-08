import Image from "next/image";
import Link from "next/link";

const STARTUP_BACKGROUND = "/game-images/Game_Startup/Game_Startup_01.png";
const GAME_LOGO = "/game-images/Game_Logo/Game_Logo_01.png";

export function StartupScreen() {
  return (
    <main className="startup-screen">
      <Image
        className="startup-background"
        src={STARTUP_BACKGROUND}
        alt=""
        aria-hidden="true"
        fill
        priority
        sizes="100vw"
        unoptimized
      />
      <div className="startup-content">
        <h1 className="startup-title">
          <Image
            className="startup-logo"
            src={GAME_LOGO}
            alt="Legends of Champions Tactics"
            width={1536}
            height={1024}
            priority
            unoptimized
          />
        </h1>
        <Link className="startup-action" href="/stages">
          <span>START GAME</span>
        </Link>
      </div>
    </main>
  );
}
