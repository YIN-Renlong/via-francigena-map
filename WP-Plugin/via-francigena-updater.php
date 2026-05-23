<?php
/**
 * Plugin Name: Via Francigena Map Updater
 * Description: 1-Click updater to pull the latest interactive map from GitHub to the /map directory.
 * Version: 1.0
 * Author: YIN Renlong
 */

if ( ! defined( 'ABSPATH' ) ) exit; // Exit if accessed directly

// 1. Add the Button to the Top Admin Bar
add_action( 'admin_bar_menu', 'vfm_add_admin_bar_button', 100 );
function vfm_add_admin_bar_button( $admin_bar ) {
    if ( ! current_user_can( 'manage_options' ) ) return; // Only admins can see this

    $admin_bar->add_node( array(
        'id'    => 'vfm-update-map',
        'title' => '🗺️ Update Francigena Map',
        'href'  => wp_nonce_url( admin_url( 'admin-post.php?action=vfm_update_map' ), 'vfm_update_nonce' ),
        'meta'  => array( 'title' => 'Pull latest version from GitHub' )
    ));
}

// 2. Handle the Button Click
add_action( 'admin_post_vfm_update_map', 'vfm_handle_update' );
function vfm_handle_update() {
    // Security check
    if ( ! current_user_can( 'manage_options' ) || ! isset( $_GET['_wpnonce'] ) || ! wp_verify_nonce( $_GET['_wpnonce'], 'vfm_update_nonce' ) ) {
        wp_die( 'Security check failed.' );
    }

    // Required WP file system tools
    require_once( ABSPATH . 'wp-admin/includes/file.php' );
    WP_Filesystem();
    global $wp_filesystem;

    $github_zip_url = 'https://github.com/YIN-Renlong/via-francigena-map/archive/refs/heads/main.zip';
    $target_dir = ABSPATH . 'map'; // The final /map folder
    $temp_dir = WP_CONTENT_DIR . '/vfm_temp_extract'; // Temporary folder for extracting

    // Step A: Download the ZIP
    $tmp_zip = download_url( $github_zip_url );
    if ( is_wp_error( $tmp_zip ) ) {
        wp_redirect( admin_url( '?vfm_status=error_download' ) );
        exit;
    }

    // Step B: Unzip to temp folder
    $unzip_result = unzip_file( $tmp_zip, $temp_dir );
    unlink( $tmp_zip ); // Delete the zip file immediately

    if ( is_wp_error( $unzip_result ) ) {
        wp_redirect( admin_url( '?vfm_status=error_unzip' ) );
        exit;
    }

    // Step C: Move files to /map and filter out backend clutter
    // The zip from GitHub puts everything in a subfolder named "via-francigena-map-main"
    $source_dir = $temp_dir . '/via-francigena-map-main';
    
    if ( ! is_dir( $target_dir ) ) {
        wp_mkdir_p( $target_dir ); // Create /map if it doesn't exist
    }

    $copy_success = vfm_recursive_copy_and_filter( $source_dir, $target_dir );

    // Step D: Cleanup temp files
    $wp_filesystem->delete( $temp_dir, true );

    // Step E: Redirect with success message
    if ( $copy_success ) {
        wp_redirect( admin_url( '?vfm_status=success' ) );
    } else {
        wp_redirect( admin_url( '?vfm_status=error_copy' ) );
    }
    exit;
}

// 3. Custom Copy Function with Filtering (Ignores .py and raw data)
function vfm_recursive_copy_and_filter( $src, $dst ) {
    $dir = opendir( $src );
    @mkdir( $dst, 0755, true );
    $success = true;

    while ( false !== ( $file = readdir( $dir ) ) ) {
        if ( ( $file != '.' ) && ( $file != '..' ) ) {
            
            // --- THE FILTER ---
            // Ignore these exact files/folders
            $blacklist = array( 'kml_raw', '.github', '.gitignore', 'README.md' );
            if ( in_array( $file, $blacklist ) ) continue;
            
            // Ignore ALL python files
            if ( pathinfo( $file, PATHINFO_EXTENSION ) === 'py' ) continue;
            // ------------------

            if ( is_dir( $src . '/' . $file ) ) {
                $res = vfm_recursive_copy_and_filter( $src . '/' . $file, $dst . '/' . $file );
                if ( !$res ) $success = false;
            } else {
                $res = copy( $src . '/' . $file, $dst . '/' . $file );
                if ( !$res ) $success = false;
            }
        }
    }
    closedir( $dir );
    return $success;
}

// 4. Show the Notification Message on Screen
add_action( 'admin_notices', 'vfm_admin_notices' );
function vfm_admin_notices() {
    if ( ! isset( $_GET['vfm_status'] ) ) return;

    $status = $_GET['vfm_status'];
    
    if ( $status === 'success' ) {
        echo '<div class="notice notice-success is-dismissible"><p>✅ <strong>Success!</strong> The Via Francigena map was successfully updated from GitHub. <a href="/map/" target="_blank">View Map</a></p></div>';
    } elseif ( $status === 'error_download' ) {
        echo '<div class="notice notice-error is-dismissible"><p>❌ <strong>Error:</strong> Could not download the ZIP file from GitHub.</p></div>';
    } elseif ( $status === 'error_unzip' ) {
        echo '<div class="notice notice-error is-dismissible"><p>❌ <strong>Error:</strong> Could not unzip the file. Check server permissions.</p></div>';
    } elseif ( $status === 'error_copy' ) {
        echo '<div class="notice notice-error is-dismissible"><p>⚠️ <strong>Warning:</strong> The file downloaded, but there was a permission error moving it to the /map directory.</p></div>';
    }
}
?>