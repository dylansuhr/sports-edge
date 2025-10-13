'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './Navigation.module.css';

export default function Navigation() {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <nav className={styles.nav}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo}>
          SPORTSEDGE
        </Link>
        <div className={styles.links}>
          <Link
            href="/signals"
            className={`${styles.link} ${isActive('/signals') ? styles.active : ''}`}
          >
            Signals
          </Link>
          <Link
            href="/performance"
            className={`${styles.link} ${isActive('/performance') ? styles.active : ''}`}
          >
            Performance
          </Link>
          <Link
            href="/progress"
            className={`${styles.link} ${isActive('/progress') ? styles.active : ''}`}
          >
            Progress
          </Link>
          <Link
            href="/paper-betting"
            className={`${styles.link} ${isActive('/paper-betting') ? styles.active : ''}`}
          >
            Paper Betting
          </Link>
          <Link
            href="/bets"
            className={`${styles.link} ${isActive('/bets') ? styles.active : ''}`}
          >
            My Bets
          </Link>
        </div>
      </div>
    </nav>
  );
}
