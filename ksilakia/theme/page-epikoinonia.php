<?php get_header(); ?>
<div class="container narrow page-wrap" style="padding-bottom:0">
<?php while ( have_posts() ) : the_post(); ?>
  <h1 class="page-title"><?php the_title(); ?></h1>
  <div class="entry-content"><?php the_content(); ?></div>
<?php endwhile; ?>
</div>
<?php get_template_part( 'parts/contact' ); get_footer(); ?>
