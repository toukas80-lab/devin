<?php get_header(); ?>
<div class="container narrow page-wrap">
<?php while ( have_posts() ) : the_post(); ?>
  <article class="post-single">
    <p class="eyebrow"><a href="<?php echo esc_url( get_permalink( get_option( 'page_for_posts' ) ) ); ?>">Οδηγοί</a> · <?php echo esc_html( get_the_date() ); ?></p>
    <h1 class="page-title"><?php the_title(); ?></h1>
    <div class="entry-content"><?php the_content(); ?></div>
    <aside class="post-cta">
      <h2>Καλαμάκια για σουβλάκια VN — άμεσα διαθέσιμα</h2>
      <p>215×3,2 · 215×4 · 240×4 mm, σακούλα 1.000 ή κούτα 10.000 τεμ. Λιανική & χονδρική.</p>
      <a class="btn" href="<?php echo esc_url( home_url( '/kalamakia-gia-souvlakia/' ) ); ?>">Δείτε τα προϊόντα</a>
    </aside>
  </article>
  <?php
  $posts = get_posts( array( 'numberposts' => 3, 'post__not_in' => array( get_the_ID() ) ) );
  if ( $posts ) : ?>
  <section class="post-related"><h2>Διαβάστε επίσης</h2><ul>
    <?php foreach ( $posts as $p ) : ?><li><a href="<?php echo esc_url( get_permalink( $p ) ); ?>"><?php echo esc_html( get_the_title( $p ) ); ?></a></li><?php endforeach; ?>
  </ul></section>
  <?php endif; ?>
<?php endwhile; ?>
</div>
<?php get_footer(); ?>
