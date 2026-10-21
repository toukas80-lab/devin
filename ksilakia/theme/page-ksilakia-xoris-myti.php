<?php get_header(); ?>
<div class="container narrow page-wrap page-blunt">
<?php while ( have_posts() ) : the_post(); ?>
  <h1 class="page-title"><?php the_title(); ?></h1>
  <img class="page-hero" src="<?php echo esc_url( get_template_directory_uri() . '/img/ksilakia-xoris-myti.jpg' ); ?>" alt="Ξυλάκια bamboo χωρίς μύτη, με ίσια κοφτή άκρη" width="1979" height="729">
  <div class="entry-content"><?php the_content(); ?></div>
<?php endwhile; ?>
</div>
<?php get_template_part( 'parts/contact' ); get_footer(); ?>
