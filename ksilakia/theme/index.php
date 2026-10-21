<?php get_header(); ?>
<div class="container narrow page-wrap">
<?php if ( have_posts() ) : ?>
  <?php if ( is_home() ) : ?>
  <h1 class="page-title">Οδηγοί για καλαμάκια, σουβλάκια & σουβλακομηχανές</h1>
  <p class="section-lead">Πρακτικές οδηγίες για ψητοπωλεία, κρεοπωλεία και βιοτεχνίες: ποιο καλαμάκι ταιριάζει σε κάθε σουβλάκι και μηχανή, πώς αποθηκεύεται και τι σημαίνουν οι πιστοποιήσεις.</p>
  <?php else : ?>
  <h1 class="page-title"><?php echo esc_html( wp_strip_all_tags( get_the_archive_title() ) ); ?></h1>
  <?php endif; ?>
  <div class="post-list">
  <?php while ( have_posts() ) : the_post(); ?>
    <article class="post-card"><h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2><?php the_excerpt(); ?><a class="more" href="<?php the_permalink(); ?>">Διαβάστε →</a></article>
  <?php endwhile; ?>
  </div>
  <?php the_posts_pagination(); ?>
<?php else : ?>
  <h1 class="page-title">Δεν βρέθηκε τίποτα</h1><p><a href="<?php echo esc_url( home_url( '/' ) ); ?>">Επιστροφή στην αρχική</a></p>
<?php endif; ?>
</div>
<?php get_footer(); ?>
