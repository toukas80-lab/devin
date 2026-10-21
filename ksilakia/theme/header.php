<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<header class="site-header">
  <div class="container nav-wrap">
    <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="logo" aria-label="ksilakia.gr αρχική">
      <?php echo ksilakia_logo_svg(); ?>
      <span>ksilakia<b>.gr</b></span>
    </a>
    <nav aria-label="Κύριο μενού">
      <?php
      if ( has_nav_menu( 'primary' ) ) {
        wp_nav_menu( array( 'theme_location' => 'primary', 'container' => false, 'items_wrap' => '<ul>%3$s</ul>', 'depth' => 1 ) );
      } else {
        echo '<a href="' . esc_url( wc_get_page_permalink( 'shop' ) ) . '">Προϊόντα</a>';
        echo '<a href="' . esc_url( ksilakia_page_url( 'xondriki-b2b' ) ) . '">Χονδρική B2B</a>';
        echo '<a href="' . esc_url( ksilakia_page_url( 'epikoinonia' ) ) . '">Επικοινωνία</a>';
      }
      if ( function_exists( 'WC' ) ) {
        echo '<a href="' . esc_url( wc_get_page_permalink( 'myaccount' ) ) . '">' . ( is_user_logged_in() ? 'Ο λογαριασμός μου' : 'Σύνδεση / Εγγραφή' ) . '</a>';
      }
      ?>
    </nav>
    <?php if ( function_exists( 'WC' ) ) : ?>
      <a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="btn btn-sm cart-link">Καλάθι <span class="count"><?php echo WC()->cart ? intval( WC()->cart->get_cart_contents_count() ) : 0; ?></span></a>
    <?php endif; ?>
    <button class="menu-toggle" aria-label="Μενού" aria-expanded="false">☰</button>
  </div>
</header>
<main>
